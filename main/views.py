from django.shortcuts import render, redirect
import json
from django.http import JsonResponse
from .forms import ImageUploadForm
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import Image, UserSession
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
import os
import cv2
import numpy as np
import math
import shutil
import traceback
import heapq
from sklearn.cluster import KMeans
from collections import defaultdict
from pycocotools import mask as mask_utils
from django.http import FileResponse
from io import BytesIO
# import torch

from segment_anything import sam_model_registry, SamAutomaticMaskGenerator

# Load the SAM model
model_type = "vit_h"  # or "vit_h" or "default", "vit_l", "vit_b", 
checkpoint_path = "models/sam_vit_h_4b8939.pth"  # VIT-H (best, slowest), # VIT-B (smallest)
sam = sam_model_registry[model_type](checkpoint=checkpoint_path)


def image_upload_view(request):
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image_file = form.cleaned_data['image']
            
            # Create a new UserSession if it doesn't exist
            session_id = request.session.get('session_id')
            if not session_id:
                user_session = UserSession.objects.create()
                request.session['session_id'] = str(user_session.session_id)
            else:
                user_session = UserSession.objects.get(session_id=session_id)
                
            
            # Modify file name to 'img_[session_id].[original-extension]'
            original_extension = os.path.splitext(image_file.name)[1]
            new_file_name = f"img_{user_session.session_id}{original_extension}"  # Use session_id instead of id
            
            image_instance = Image(session=user_session, image=image_file)
            
            if user_session.images.count() == 0:  # Check if this is the first image in the session
                image_instance.is_original = True
            image_instance.image.save(new_file_name, image_file, save=False)
            image_instance.save()
            
            # Save the image to the Image model
            # image_instance = Image(session=user_session, image=image_file)
            # image_instance.save()
                        
            # The file is now saved, and 'image_instance.image' holds the correct path
            image_url = image_instance.image.url
                        
            # Calculate histogram
            image_path = image_instance.image.path  # Use the path from the Image instance
            img = cv2.imread(image_path)

            histogram_data = {}
            # Check if the image is grayscale
            if len(img.shape) == 2 or (img.shape[2] == 3 and np.allclose(img[:, :, 0], img[:, :, 1]) and np.allclose(img[:, :, 1], img[:, :, 2])):
                hist = cv2.calcHist([img], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                # Calculate histogram for each channel
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()
            


            return JsonResponse({
                'success': True,
                'url': image_url,
                'image_id': image_instance.id,  # Return the image ID
                'histogram': histogram_data
            })
    else:
        form = ImageUploadForm()
    
    return render(request, 'home_page.html', {'form': form})




@csrf_exempt
def delete_image(request):
    if request.method == 'POST':
        # Since we're using sendBeacon, we need to manually parse the form data.
        # If you're sending JSON with sendBeacon, you would instead load the JSON data here.
        image_id = request.POST.get('image_id')
        
        if not image_id:
            # If for some reason, image_id is not provided, log an error or handle it as per your requirements.
            return JsonResponse({'error': 'No image ID provided'}, status=400)
        
        try:
            # Retrieve the original image instance. Adjust this if your image_id needs to be cast to a different type.
            original_image = Image.objects.get(id=image_id)
            
            # Retrieve all images in the session of this image.
            images_to_delete = Image.objects.filter(session=original_image.session)
            
            for image in images_to_delete:
                # This will delete the image file and the model instance if your model's delete method is set up to do so.
                image.delete()
            
            # Optionally, if you want to delete the session as well:
            original_image.session.delete()

            return JsonResponse({'success': True})
        except Image.DoesNotExist:
            return JsonResponse({'error': 'Image not found'}, status=404)
        except Exception as e:
            # For debugging purposes, log the exception.
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)



@require_http_methods(["GET"])
def check_image_view(request):
    session_id = request.session.get('session_id')
    if session_id:
        user_session = UserSession.objects.filter(session_id=session_id).first()
        if user_session:
            image = user_session.images.filter(is_original=True).first()
            if image:
                return JsonResponse({'url': image.image.url}, status=200)
    return JsonResponse({'url': None}, status=200)





@csrf_exempt
def equalize_histogram(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)

            # Fetch the latest image version from the session
            latest_image_instance = user_session.images.order_by('-version').first()

            if not latest_image_instance:
                return JsonResponse({'error': 'Image not found in session'}, status=404)

            # Read the latest image version using OpenCV
            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)


            # Apply histogram equalization
            if len(img.shape) == 2:  # Grayscale image
                img_eq = cv2.equalizeHist(img)
            else:  # Color image
                img_yuv = cv2.cvtColor(img, cv2.COLOR_BGR2YUV)
                img_yuv[:,:,0] = cv2.equalizeHist(img_yuv[:,:,0])
                img_eq = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)

            # Determine the new file name
            original_image_instance = user_session.images.filter(is_original=True).first()
            eq_count = user_session.images.filter(image__contains=f"eq_{original_image_instance.id}").count() + 1
            new_file_name = f"equalized_uploads/eq_{original_image_instance.id}_{eq_count}.png"

            # Save the equalized image as a new version
            _, img_encoded = cv2.imencode('.png', img_eq)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Calculate the new histogram data
            histogram_data = {}  
            if len(img_eq.shape) == 2 or (img_eq.shape[2] == 3 and np.allclose(img_eq[:, :, 0], img_eq[:, :, 1]) and np.allclose(img_eq[:, :, 1], img_eq[:, :, 2])):
                hist = cv2.calcHist([img_eq], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_eq], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        # Log the full traceback for more detailed error information
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)






@csrf_exempt
def apply_log_transformation(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            original_image_instance = user_session.images.filter(is_original=True).first()

            if not original_image_instance:
                return JsonResponse({'error': 'Original image not found in session'}, status=404)

            # Fetch the latest image version from the session
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Apply log transformation
            c_value = float(request.POST.get('c_value'))
            c = c_value
            img_transformed = c * np.log(1 + np.float32(img))  # Ensuring input is float for log transformation
            img_transformed = cv2.normalize(img_transformed, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)

            # Determine the new file name
            lt_count = user_session.images.filter(image__contains=f"lt_{original_image_instance.id}").count() + 1
            new_file_name = f"log_transformed_uploads/lt_{original_image_instance.id}_{lt_count}.png"

            # Save the transformed image as a new version
            _, img_encoded = cv2.imencode('.png', img_transformed)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Calculate the new histogram data
            histogram_data = {}
            if len(img_transformed.shape) == 2 or (img_transformed.shape[2] == 3 and np.allclose(img_transformed[:, :, 0], img_transformed[:, :, 1]) and np.allclose(img_transformed[:, :, 1], img_transformed[:, :, 2])):
                hist = cv2.calcHist([img_transformed], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_transformed], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
def apply_power_law_transformation(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            c_value = float(request.POST.get('c_value'))
            y_value = float(request.POST.get('y_value'))

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Apply Power-Law Transformation
            img_transformed = c_value * np.power(img, y_value)
            img_transformed = np.clip(img_transformed, 0, 255).astype(np.uint8)

            # Determine the new file name
            pl_count = user_session.images.filter(image__contains=f"pl_{latest_image_instance.id}").count() + 1
            new_file_name = f"powerlaw_uploads/pl_{latest_image_instance.id}_{pl_count}.png"

            # Save the transformed image as a new version
            _, img_encoded = cv2.imencode('.png', img_transformed)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            histogram_data = {}
            if len(img_transformed.shape) == 2 or (img_transformed.shape[2] == 3 and np.allclose(img_transformed[:, :, 0], img_transformed[:, :, 1]) and np.allclose(img_transformed[:, :, 1], img_transformed[:, :, 2])):
                hist = cv2.calcHist([img_transformed], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_transformed], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def apply_image_negative(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Apply Image Negative
            max_intensity = np.iinfo(img.dtype).max
            img_negative = max_intensity - img

            # Determine the new file name
            neg_count = user_session.images.filter(image__contains=f"neg_{latest_image_instance.id}").count() + 1
            new_file_name = f"negative_uploads/neg_{latest_image_instance.id}_{neg_count}.png"

            # Save the negative image as a new version
            _, img_encoded = cv2.imencode('.png', img_negative)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            #histogram_data = calculate_histogram(img_negative)
            
            histogram_data = {}
            if len(img_negative.shape) == 2 or (img_negative.shape[2] == 3 and np.allclose(img_negative[:, :, 0], img_negative[:, :, 1]) and np.allclose(img_negative[:, :, 1], img_negative[:, :, 2])):
                hist = cv2.calcHist([img_negative], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_negative], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def apply_spatial_filter(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            kernel_type = request.POST.get('kernel_type')
            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            if kernel_type == 'sharpening':
                kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            elif kernel_type == 'blurring':
                kernel = cv2.getGaussianKernel(3, 0)
                kernel = np.outer(kernel, kernel.transpose())
            else:
                return JsonResponse({'error': 'Invalid kernel type'}, status=400)

            img_filtered = cv2.filter2D(img, -1, kernel, borderType=cv2.BORDER_REPLICATE)

            # Determine the new file name
            sf_count = user_session.images.filter(image__contains=f"sf_{latest_image_instance.id}").count() + 1
            new_file_name = f"spatial_uploads/sf_{latest_image_instance.id}_{sf_count}_{kernel_type}.png"

            # Save the filtered image as a new version
            _, img_encoded = cv2.imencode('.png', img_filtered)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            # histogram_data = calculate_histogram(img_filtered)
            
            histogram_data = {}
            if len(img_filtered.shape) == 2 or (img_filtered.shape[2] == 3 and np.allclose(img_filtered[:, :, 0], img_filtered[:, :, 1]) and np.allclose(img_filtered[:, :, 1], img_filtered[:, :, 2])):
                hist = cv2.calcHist([img_filtered], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_filtered], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
def apply_mean_average_filter(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Apply Mean/Average Filter
            kernel = np.ones((3, 3), np.float32) / 9  # 3x3 Mean/Average filter
            img_filtered = cv2.filter2D(img, -1, kernel, borderType=cv2.BORDER_REPLICATE)

            # Determine the new file name
            ma_count = user_session.images.filter(image__contains=f"ma_{latest_image_instance.id}").count() + 1
            new_file_name = f"meanaverage_uploads/ma_{latest_image_instance.id}_{ma_count}.png"

            # Save the filtered image as a new version
            _, img_encoded = cv2.imencode('.png', img_filtered)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            # histogram_data = calculate_histogram(img_filtered)
            histogram_data = {}
            if len(img_filtered.shape) == 2 or (img_filtered.shape[2] == 3 and np.allclose(img_filtered[:, :, 0], img_filtered[:, :, 1]) and np.allclose(img_filtered[:, :, 1], img_filtered[:, :, 2])):
                hist = cv2.calcHist([img_filtered], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_filtered], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()
            

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)




@csrf_exempt
def apply_median_filter(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Apply Median Filter
            img_filtered = cv2.medianBlur(img, 3)  # 3x3 Median filter

            # Determine the new file name
            median_count = user_session.images.filter(image__contains=f"median_{latest_image_instance.id}").count() + 1
            new_file_name = f"median_uploads/median_{latest_image_instance.id}_{median_count}.png"

            # Save the filtered image as a new version
            _, img_encoded = cv2.imencode('.png', img_filtered)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            # histogram_data = calculate_histogram(img_filtered)
            
            histogram_data = {}
            if len(img_filtered.shape) == 2 or (img_filtered.shape[2] == 3 and np.allclose(img_filtered[:, :, 0], img_filtered[:, :, 1]) and np.allclose(img_filtered[:, :, 1], img_filtered[:, :, 2])):
                hist = cv2.calcHist([img_filtered], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_filtered], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()
            

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def apply_nearest_neighbor_interpolation(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            scaling_factor = int(request.POST.get('scaling_factor')) / 100.0
            # Check if scaling factor is within the allowed range
            if scaling_factor < 0.1 or scaling_factor > 2.0:
                return JsonResponse({'error': 'Scaling factor must be between 10% and 200%'}, status=400)
            
            
            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Calculate new dimensions
            new_width = int(img.shape[1] * scaling_factor)
            new_height = int(img.shape[0] * scaling_factor)
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_NEAREST)

            # Determine the new file name
            nni_count = user_session.images.filter(image__contains=f"nni_{latest_image_instance.id}").count() + 1
            new_file_name = f"nni_uploads/nni_{latest_image_instance.id}_{nni_count}.png"

            # Save the scaled image as a new version
            _, img_encoded = cv2.imencode('.png', img_resized)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            #histogram_data = calculate_histogram(img_resized)
            histogram_data = {}
            if len(img_resized.shape) == 2 or (img_resized.shape[2] == 3 and np.allclose(img_resized[:, :, 0], img_resized[:, :, 1]) and np.allclose(img_resized[:, :, 1], img_resized[:, :, 2])):
                hist = cv2.calcHist([img_resized], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_resized], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()
            

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)





@csrf_exempt
def apply_bilinear_interpolation(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            scaling_factor = int(request.POST.get('scaling_factor')) / 100.0

            # Validate the scaling factor
            if scaling_factor < 0.1 or scaling_factor > 2.0:
                return JsonResponse({'error': 'Scaling factor must be between 10% and 200%'}, status=400)

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            # Calculate new dimensions and apply bilinear interpolation
            new_width = int(img.shape[1] * scaling_factor)
            new_height = int(img.shape[0] * scaling_factor)
            img_resized = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

            # Determine the new file name
            bilinear_count = user_session.images.filter(image__contains=f"bilinear_{latest_image_instance.id}").count() + 1
            new_file_name = f"bilinear_uploads/bilinear_{latest_image_instance.id}_{bilinear_count}.png"

            # Save the scaled image as a new version
            _, img_encoded = cv2.imencode('.png', img_resized)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            # Recalculate the histogram data
            # histogram_data = calculate_histogram(img_resized)
            histogram_data = {}
            if len(img_resized.shape) == 2 or (img_resized.shape[2] == 3 and np.allclose(img_resized[:, :, 0], img_resized[:, :, 1]) and np.allclose(img_resized[:, :, 1], img_resized[:, :, 2])):
                hist = cv2.calcHist([img_resized], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img_resized], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()

            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)






def rle_compress(img):
    """
    Compresses an image using Run-Length Encoding.
    """
    flat_img = img.flatten()
    result = []
    count = 1
    prev = flat_img[0]
    for pixel in flat_img[1:]:
        if pixel == prev:
            count += 1
        else:
            result.append((prev, count))
            count = 1
            prev = pixel
    result.append((prev, count))
    return result

def apply_rle_compression(request):
    try:
        if request.method == 'GET':
            session_id = request.session.get('session_id')
            if not session_id:
                return HttpResponse('Session not found', status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale for simplicity

            compressed_data = rle_compress(img)

            # Create a string representation of the compressed data
            # compressed_str = '\n'.join([f'{pixel_val} {count}' for pixel_val, count in compressed_data])
            
            # Include dimensions in the compressed string
            height, width = img.shape
            compressed_str = f"{height} {width}\n"  # Prepend dimensions
            compressed_str += '\n'.join([f'{pixel_val} {count}' for pixel_val, count in compressed_data])

            response = HttpResponse(compressed_str, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="rle_enc_img.txt"'
            return response
    except Exception as e:
        return HttpResponse(str(e), status=500)





def huffman_encoding(data):
    """
    Perform Huffman encoding on the data.
    """
    frequency = defaultdict(int)
    for symbol in data:
        frequency[symbol] += 1

    heap = [[weight, [symbol, ""]] for symbol, weight in frequency.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        lo = heapq.heappop(heap)
        hi = heapq.heappop(heap)
        for pair in lo[1:]:
            pair[1] = '0' + pair[1]
        for pair in hi[1:]:
            pair[1] = '1' + pair[1]
        heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])
    huffman_tree = sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

    huffman_code = {symbol: code for symbol, code in huffman_tree}
    return huffman_code





def apply_huffman_coding(request):
    try:
        if request.method == 'GET':
            session_id = request.session.get('session_id')
            if not session_id:
                return HttpResponse('Session not found', status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()

            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)  # Convert to grayscale for simplicity
            flat_img = img.flatten()

            # Apply Huffman Coding
            huffman_code = huffman_encoding(flat_img)
            encoded_data = ''.join(huffman_code[pixel] for pixel in flat_img)
            
            # Include dimensions in the compressed string
            height, width = img.shape
            compressed_str = f"{height} {width}\n\n"  # Prepend dimensions with double newline

            # Append Huffman codes and encoded data with necessary separators
            codes_str = '\n'.join([f'{key}:{value}' for key, value in huffman_code.items()])
            compressed_str += codes_str + '\n\n' + encoded_data  # Separate codes and data with double newline

            response = HttpResponse(compressed_str, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename="huffman_encoded_image.txt"'
            return response
    except Exception as e:
        return HttpResponse(str(e), status=500)




@csrf_exempt
def decode_and_preview(request):
    try:
        if request.method == 'POST':
            decode_option = request.POST.get('decodeoption')
            uploaded_file = request.FILES.get('codedFile')

            if not uploaded_file.name.endswith('.txt'):
                return JsonResponse({'error': 'File format not supported'}, status=400)

            # Read the content of the file
            file_content = uploaded_file.read().decode('utf-8')

            if decode_option == 'rledecode':
                decoded_img = rle_decode(file_content)  # Implement this function
            elif decode_option == 'huffdecode':
                decoded_img = huffman_decode(file_content)  # Implement this function
            else:
                return JsonResponse({'error': 'Invalid decoding option'}, status=400)

            # Call the upload_decoded_image view
            return upload_decoded_image(request, decoded_img, request.session.get('session_id'))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




def rle_decode(encoded_str):
    # Split the encoded string into lines
    lines = encoded_str.strip().split('\n')

    # Extract dimensions
    height, width = map(int, lines.pop(0).split())

    # Continue with decoding logic...
    decoded_data = []
    for line in lines:
        pixel_value, count = map(int, line.split())
        decoded_data.extend([pixel_value] * count)

    # Reshape the flat list into a 2D array using extracted dimensions
    decoded_image = np.array(decoded_data, dtype=np.uint8).reshape((height, width))

    return decoded_image



def huffman_decode(encoded_str):
    try:
        parts = encoded_str.split('\n\n')
        if len(parts) < 3:
            print("Encoded string format is incorrect.")
            return None
        dimension_info, codes_str, encoded_image_data = parts[0], parts[1], parts[2]

        height, width = map(int, dimension_info.split())
        print(f"Decoding image of dimensions: {height}x{width}")

        huffman_codes = {}
        for line in codes_str.split('\n'):
                if ':' not in line:
                    print(f"Invalid line in Huffman codes: {line}")
                    continue
                symbol, code = line.split(':')
                huffman_codes[code] = int(symbol)

        decoded_data = []
        code = ''
        for bit in encoded_image_data:
            code += bit
            if code in huffman_codes:
                decoded_data.append(huffman_codes[code])
                code = ''
            elif len(code) > max(len(c) for c in huffman_codes):
                print(f"Invalid Huffman code encountered: {code}")
                break

        if len(decoded_data) != height * width:
            print(f"Warning: Decoded data length ({len(decoded_data)}) does not match expected size ({height * width})")

        decoded_image = np.array(decoded_data, dtype=np.uint8).reshape((height, width))
        return decoded_image
    except Exception as e:
        print(f"Error in Huffman decoding: {e}")
        return None






def upload_decoded_image(request, decoded_img_array, session_id):
    """
    Handle uploading of the decoded image.
    """
    try:
        # Convert the decoded image array to an image file
        _, img_encoded = cv2.imencode('.png', decoded_img_array)
        new_image_file = ContentFile(img_encoded.tobytes(), name="decoded_image.png")

        # Retrieve or create a UserSession
        if not session_id:
            user_session = UserSession.objects.create()
            request.session['session_id'] = str(user_session.session_id)
        else:
            user_session = UserSession.objects.get(session_id=session_id)

        # Save the new image file as a user upload
        image_instance = Image(session=user_session, image=new_image_file, is_original=True)
        image_instance.save()

        # Calculate histogram
        histogram_data = {}  # [Add histogram calculation logic here]
        

        return JsonResponse({
            'url': image_instance.get_absolute_url(),
            'image_id': image_instance.id,
            'histogram': histogram_data
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)




# Experimental
@csrf_exempt
def apply_segmentation(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            segmentation_type = request.POST.get('segmentation_type', 'thresholding')
            
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            latest_image_instance = user_session.images.order_by('-version').first()
            img_path = latest_image_instance.image.path
            img = cv2.imread(img_path)

            if segmentation_type == 'thresholding':
                segmented_img = apply_thresholding(img)
            elif segmentation_type == 'edgedetection':
                segmented_img = apply_edge_detection(img)
            elif segmentation_type == 'clustering':
                segmented_img = apply_kmeans_clustering(img)
            elif segmentation_type == 'sam':
                segmented_img = apply_sam_segmentation(img)
            else:
                return JsonResponse({'error': 'Invalid segmentation type'}, status=400)

            # Determine the new file name
            segmentation_count = user_session.images.filter(image__contains=f"segmentation_{latest_image_instance.id}").count() + 1
            new_file_name = f"segmentation_uploads/segmentation_{latest_image_instance.id}_{segmentation_count}.png"

            # Save the segmented image as a new version
            _, img_encoded = cv2.imencode('.png', segmented_img)
            new_image_file = ContentFile(img_encoded.tobytes(), name=new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_file, version=latest_image_instance.version + 1)
            new_image_instance.save()

            return JsonResponse({'url': new_image_instance.get_absolute_url()})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)



def apply_thresholding(img):
    # Convert to grayscale if the image is colored
    if len(img.shape) == 3:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray_img = img

    # Apply thresholding
    _, thresholded_img = cv2.threshold(gray_img, 127, 255, cv2.THRESH_BINARY)

    # If needed, convert back to color (3 channels) to maintain consistency
    if len(img.shape) == 3:
        thresholded_img = cv2.cvtColor(thresholded_img, cv2.COLOR_GRAY2BGR)

    return thresholded_img




def apply_edge_detection(img):
    # Convert to grayscale if the image is colored
    if len(img.shape) == 3:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray_img = img

    # Apply Canny Edge Detector
    edges = cv2.Canny(gray_img, 100, 200)  # These values can be adjusted

    # Optional: Convert edges back to 3 channels to maintain consistency with color images
    if len(img.shape) == 3:
        edges_colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return edges_colored

    return edges




def apply_kmeans_clustering(img, k=3):
    # Reshape the image to a 2D array of pixels
    pixel_values = img.reshape((-1, 3))  # Assuming the image is in BGR format
    pixel_values = np.float32(pixel_values)

    # Apply KMeans clustering
    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(pixel_values)

    # Replace each pixel value with its corresponding cluster center value
    centers = np.uint8(kmeans.cluster_centers_)
    labels = kmeans.labels_
    segmented_image = centers[labels.flatten()]
    segmented_image = segmented_image.reshape(img.shape)

    return segmented_image



def apply_sam_segmentation(img):
    # Initialize the SAM model and mask generator
    mask_generator = SamAutomaticMaskGenerator(sam)
    
    # Generate masks for the image
    masks = mask_generator.generate(img)

    # Apply masks to the image
    segmented_img = apply_masks_to_image(img, masks)

    return segmented_img





def apply_masks_to_image(img, masks):
    for mask_dict in masks:
        # Extract the binary mask array
        binary_mask = mask_dict['segmentation']

        # Generate a random color for the mask
        color = np.random.randint(0, 256, (1, 3), dtype=np.uint8)

        # Overlay the binary mask on the image using the random color
        img[binary_mask] = img[binary_mask] * 0.5 + color * 0.5

    return img









# Revert button veiw
@csrf_exempt
def revert_image(request):
    try:
        if request.method == 'POST':
            session_id = request.session.get('session_id')
            if not session_id:
                return JsonResponse({'error': 'Session not found'}, status=400)

            user_session = UserSession.objects.get(session_id=session_id)
            # Ensure this is the original image
            original_image_instance = user_session.images.filter(is_original=True).first()

            if not original_image_instance:
                return JsonResponse({'error': 'Original image not found in session'}, status=404)

            # Count the number of times the image has been reverted
            rev_count = user_session.images.filter(image__contains=f"rev_{original_image_instance.id}").count() + 1

            # Create a new file name for the reverted image
            original_extension = os.path.splitext(original_image_instance.image.name)[1]
            new_file_name = f"rev_{original_image_instance.id}_{rev_count}{original_extension}"

            # Ensure the destination directory exists inside 'uploads'
            new_image_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'reverted_uploads')
            if not os.path.exists(new_image_dir):
                os.makedirs(new_image_dir)

            # Copy the original image to the reverted location
            original_image_path = original_image_instance.image.path
            new_image_path = os.path.join(new_image_dir, new_file_name)
            shutil.copy2(original_image_path, new_image_path)

            # Save the reverted image as a new version
            new_image_rel_path = os.path.join('uploads', 'reverted_uploads', new_file_name)
            new_image_instance = Image(session=user_session, image=new_image_rel_path, version=original_image_instance.version + 1, is_original=False)
            new_image_instance.save()

            # Recalculate the histogram for the reverted image
            img = cv2.imread(new_image_path)
            
            # Calculate the new histogram data
            histogram_data = {}
            if len(img.shape) == 2 or (img.shape[2] == 3 and np.allclose(img[:, :, 0], img[:, :, 1]) and np.allclose(img[:, :, 1], img[:, :, 2])):
                hist = cv2.calcHist([img], [0], None, [256], [0, 256])
                histogram_data['Intensity'] = hist.flatten().tolist()
            else:
                for i, col in enumerate(['Blue', 'Green', 'Red']):
                    hist = cv2.calcHist([img], [i], None, [256], [0, 256])
                    histogram_data[col] = hist.flatten().tolist()
            
            
            return JsonResponse({
                'url': new_image_instance.get_absolute_url(),
                'histogram': histogram_data
            })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)





@require_http_methods(["GET"])
def download_image(request, format):
    try:
        session_id = request.session.get('session_id')
        if not session_id:
            return JsonResponse({'error': 'Session not found'}, status=400)

        user_session = UserSession.objects.get(session_id=session_id)
        latest_image_instance = user_session.images.order_by('-version').first()

        if not latest_image_instance:
            return JsonResponse({'error': 'No image found'}, status=404)

        img_path = latest_image_instance.image.path
        img = cv2.imread(img_path)

        # Convert the image to the requested format and prepare for download
        _, img_buffer = cv2.imencode(f'.{format}', img)
        buffer = BytesIO(img_buffer)

        # Send the in-memory image data as response
        response = HttpResponse(buffer.getvalue(), content_type=f'image/{format}')
        response['Content-Disposition'] = f'attachment; filename="downloaded_image.{format}"'
        return response
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)



@require_http_methods(["GET"])
def get_original_image_url(request):
    session_id = request.session.get('session_id')
    if not session_id:
        return JsonResponse({'error': 'Session not found'}, status=400)

    user_session = UserSession.objects.get(session_id=session_id)
    original_image_instance = user_session.images.filter(is_original=True).first()

    if not original_image_instance:
        return JsonResponse({'error': 'Original image not found'}, status=404)

    return JsonResponse({'url': original_image_instance.image.url})



# Homepage
def home(request):
    # Clear session data related to images
    request.session.pop('uploaded_images', None)
    request.session.pop('session_id', None)
    context = {}
    return render(request, "home_page.html", context)


