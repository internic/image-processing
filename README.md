
# Image Processing Web App

This Django-based image processing application provides a user-friendly interface for performing various image processing operations. It allows users to upload images and apply different algorithms like histogram equalization, log transformation, spatial filtering, and more. The app is designed to be intuitive and provides real-time visual feedback for each operation.

<p float="left">
  <img src="Screenshot_1.png?raw=true" width="100%" />
</p>

## Features

- **Image Upload:** Users can upload images for processing.
- **Real-Time Image Processing:** Apply various image processing algorithms and see the results instantly.
- **Before/After Comparison:** A slider to compare the original and edited images side-by-side.
- **Algorithm Application:** Support for multiple algorithms including histogram equalization, log transformation, power-law transformation, image negative, segmentation, and more.
- **Image Download:** Download the processed images in different formats like JPEG, PNG, and WEBP.
- **Image Encoding/Decoding:** Run-Length Encoding (RLE) and Huffman Coding for image compression and decompression.
- **Image Segmentation with Neural Network (SAM):** Segment the images with MetaAi Segment Anything Model (Download required)

## Installation

### Prerequisites

- Python 3.x
- Django
- Other dependencies in `requirements.txt`

### Steps

1. Clone the repository:
```
git clone https://github.com/internic/image-processing.git
```
2. Navigate to the project directory:
```
cd image-processing
```
2.1. Create virtual environment:
```
python -m venv .venv (or any other way for your system)
```
2.2. Activate your newly created virtual environment:
```
source .venv/bin/activate (or any other specific command for your system)
```
3. Install the required packages:
```
pip install -r requirements.txt
```
4. For image segmentation with NN functionality, please download MetaAi Segment Anything pretrained Model:
```
direct download link https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
or simply go to https://github.com/facebookresearch/segment-anything/tree/main find the ViT-H SAM model link and download it
once the model is downloaded put it in project's "models" folder
```
5. Run the Django development server:
```
python manage.py runserver
```


## Usage

1. **Uploading an Image:** Click the upload button and select an image to begin processing.
2. **Applying Algorithms:** Choose an algorithm from the available options and apply it to the image.
3. **Comparing Edits:** Use the Before/After slider to compare the edited image with the original.
4. **Downloading Images:** Download the edited image in your preferred format.
5. **Encoding/Decoding:** Compress images using RLE or Huffman Coding and decompress them back.

## Supported Algorithms

- Histogram Equalization
- Log Transformation
- Power-Law Transformation
- Image Negative
- Spatial Filtering (Sharpening, Blurring)
- Mean/Average Filtering
- Median Filtering
- Nearest Neighbor Interpolation
- Bilinear Interpolation
- Run-Length Encoding (RLE)
- Huffman Coding
- Maybe some other will come soon

## Notes

The code is not fully optimized, so there may be some bugs

## Contributing

Contributions to this project are welcome. Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the [MIT License](LICENSE).


