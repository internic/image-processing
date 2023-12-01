from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path('upload-image/', views.image_upload_view, name='upload-image'),
    path('check-image/', views.check_image_view, name='check-image'),
    path('equalize-histogram/', views.equalize_histogram, name='equalize_histogram'),
    path('delete-image/', views.delete_image, name='delete_image'),
    path('apply-log-transformation/', views.apply_log_transformation, name='apply_log_transformation'),
    path('revert-image/', views.revert_image, name='revert_image'),
    path('apply-power-law-transformation/', views.apply_power_law_transformation, name='apply_power_law_transformation'),
    path('apply-image-negative/', views.apply_image_negative, name='apply_image_negative'),
    path('apply-spatial-filter/', views.apply_spatial_filter, name='apply_spatial_filter'),
    path('apply-mean-average-filter/', views.apply_mean_average_filter, name='apply_mean_average_filter'),
    path('apply-median-filter/', views.apply_median_filter, name='apply_median_filter'),
    path('apply-nearest-neighbor-interpolation/', views.apply_nearest_neighbor_interpolation, name='apply_nearest_neighbor_interpolation'),
    path('apply-bilinear-interpolation/', views.apply_bilinear_interpolation, name='apply_bilinear_interpolation'),
    path('apply-rle-compression/', views.apply_rle_compression, name='apply_rle_compression'),
    path('apply-huffman-coding/', views.apply_huffman_coding, name='apply_huffman_coding'),
    path('decode-and-preview/', views.decode_and_preview, name='decode_and_preview'),
    path('apply-segmentation/', views.apply_segmentation, name='apply_segmentation'),
    path('download-image/<str:format>/', views.download_image, name='download_image'),
    
    path('get-original-image/', views.get_original_image_url, name='get_original_image_url'),
]
