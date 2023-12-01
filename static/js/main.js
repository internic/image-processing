
$(document).ready(function() {
    
    "use strict";
    const submenu_animation_speed = 200;

    const delay = (function(){
        var timer = 0;
        return function(callback, ms){
            clearTimeout (timer);
            timer = setTimeout(callback, ms);
        };
    })();

  



    function toggleSidebar() {
        $('body').toggleClass("sidebar-hidden");
    };

    function toggleCollapsedSidebar() {
        $('body').toggleClass("page-sidebar-collapsed");

        const container = document.querySelector('.page-sidebar .accordion-menu');
        const ps = new PerfectScrollbar(container);

        if($('body').hasClass('page-sidebar-collapsed')) {
            ps.destroy();
        }
    };

    $('#sidebar-toggle').on('click', function() {
        toggleSidebar();
    });

    $('#sidebar-collapsed-toggle').on('click', function() {
        toggleCollapsedSidebar();
    });

    $('.close-search').on('click', function() {
        $('body').removeClass('search-show');
    });
    
    $('#toggle-search').on('click', function() {
        $('body').addClass('search-show');
    });
    
    (function(){ 
        feather.replace()
    })();

    function global() {

        $('[data-bs-toggle="popover"]').popover();
        $('[data-bs-toggle="tooltip"]').tooltip(); // gives the scroll position


        // Form Validation
        var forms = document.querySelectorAll('.needs-validation');

        // Loop over them and prevent submission
        Array.prototype.slice.call(forms)
            .forEach(function (form) {
                form.addEventListener('submit', function (event) {
                    if (!form.checkValidity()) {
                        event.preventDefault();
                        event.stopPropagation();
                    }

                    form.classList.add('was-validated');
                }, false);
            });
    }

    const activitySidebar = function() {
        $('#activity-sidebar-toggle').on('click', function(e) {
            $('body').toggleClass('activity-sidebar-show')
            e.preventDefault()
        })

        $('.activity-sidebar-overlay').on('click', function(e) {
            $('body').toggleClass('activity-sidebar-show')
        })

        $('#activity-sidebar-close').on('click', function(e) {
            $('body').removeClass('activity-sidebar-show')
        })
    }

    //searchResults();
    // sidebar();
    global();
    activitySidebar();



});

$(window).on("load", function () {
    setTimeout(function() {
    $('body').addClass('no-loader')}, 1000)
});



document.addEventListener('DOMContentLoaded', function() {
  // Function to remove the 'active-page' class from all nav items and hide all divs
  function resetActiveState() {
    document.querySelectorAll('.nav-lnk').forEach(function(navItem) {
      navItem.classList.remove('active-page');
    });
    document.querySelectorAll('.itm').forEach(function(div) {
      div.classList.add('hidden');
    });
  }

  // Function to set the active nav item and show the related divs
  function setActive(navItem) {
    resetActiveState(); // First, reset the active states

    // Add 'active-page' to the clicked nav item
    navItem.classList.add('active-page');

    // Get the target class from the data-target attribute
    const targetClass = navItem.getAttribute('data-target');

    // Update the page title
    const pageTitle = navItem.querySelector('a').textContent.trim();
    document.getElementById('page-title').textContent = pageTitle;

    // Select all divs that should be shown and remove the 'hidden' class
    document.querySelectorAll('.' + targetClass).forEach(function(div) {
      div.classList.remove('hidden');
    });
  }

  // Add click event listeners to all nav items
  document.querySelectorAll('.nav-lnk').forEach(function(navItem) {
    navItem.addEventListener('click', function(event) {
      event.preventDefault(); // Prevent default link behavior
      setActive(navItem); // Set this nav item as active
    });
  });

  // Set the default active content
  const defaultActiveNavItem = document.querySelector('.nav-lnk.active-page');
  if (defaultActiveNavItem) {
    setActive(defaultActiveNavItem);
  }
});



// Image upload & drag and drop & histogram handling new version

document.addEventListener('DOMContentLoaded', function() {
    var uploadField = document.getElementById('upload');
    var form = document.getElementById('image-upload-form');
    var area = document.querySelector('.area');
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    var uploadedImage = document.getElementById('uploaded-image');
    var chartContainer = document.querySelector("#chartX");

    // Initialize the chart with dummy data
    var chart = new ApexCharts(chartContainer, getChartOptions([]));
    chart.render();

    function getChartOptions(seriesData) {
        return {
            series: seriesData,
            chart: {
                type: 'bar',
                height: 420
            },
            dataLabels: {
                enabled: false
            },
            plotOptions: {
                bar: {
                    barHeight: '80%',
                }
            },
            xaxis: {
                tickAmount: 6,
                labels: {
                    formatter: function(val) {
                        return Math.round(val);
                    },
                    style: {
                        colors: 'rgba(154, 156, 171, 1)'
                    },
                }
            },
            yaxis: {
                labels: {
                    style: {
                        colors: 'rgba(154, 156, 171, 1)'
                    },
                },
            },
            tooltip: {
                shared: true,
                intersect: false
            },
            grid: {
                borderColor: 'rgba(154, 156, 171, 1)',
                strokeDashArray: 4
            },
            legend: {
                labels: {
                    colors: 'rgba(154, 156, 171, 1)'
                },
            },
        };
    }

    function updateChart(histogram) {
        let series = [];
        if (Object.keys(histogram).length === 1 && histogram['Intensity']) {
            // Grayscale image
            series.push({
                name: 'Intensity',
                data: histogram['Intensity'],
                color: '#CCC'
            });
        } else {
            // Color image
            series.push({
                name: 'Red',
                data: histogram['Red'],
                color: '#FF4560'
            });
            series.push({
                name: 'Green',
                data: histogram['Green'],
                color: '#00E396'
            });
            series.push({
                name: 'Blue',
                data: histogram['Blue'],
                color: '#008FFB'
            });
        }
        chart.updateOptions(getChartOptions(series));
    }


    function uploadFile(file) {
        var formData = new FormData();
        formData.append('image', file);

        fetch('/upload-image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Server responded with a status: ' + response.status);
            }
        })
        .then(data => {
            console.log(data);
            if(data.success) {
                uploadedImage.src = data.url;
                uploadedImage.style.display = 'block';
                
                if ('image_id' in data) {
                    console.log('Image ID:', data.image_id);
                    uploadedImage.setAttribute('data-image-id', data.image_id);
                } else {
                    console.error('Image ID is missing from the response');
                }

                form.style.display = 'none';
                area.style.display = 'none'; // Hide the drag and drop area
                if (!uploadedImage.id) {
                    uploadedImage.id = 'uploaded-image';
                    area.appendChild(uploadedImage);
                }
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            }
        })

        .catch(error => {
            console.error('Error:', error);
            alert('There was an error uploading the file.');
        });
    }

    function handleFile(file) {
        if (file.type.match('image.*')) {
            if (file.size <= (6 * 1024 * 1024)) { // 6MB limit
                uploadFile(file);
            } else {
                alert('File is too large. Please select a file smaller than 6MB.');
            }
        } else {
            alert('Invalid file type. Please select an image file.');
        }
    }

    uploadField.addEventListener('change', function(e) {
        handleFile(e.target.files[0]);
    }, false);

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        area.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        area.addEventListener(eventName, unhighlight, false);
    });

    function highlight(e) {
        area.classList.add('highlight');
    }

    function unhighlight(e) {
        area.classList.remove('highlight');
    }

    area.addEventListener('drop', function(e) {
        var dt = e.dataTransfer;
        var file = dt.files[0];
        handleFile(file);
    }, false);

    function checkForUploadedImage() {
        fetch('/check-image/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken,
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                uploadedImage.style.display = 'block';
                form.style.display = 'none';
                area.style.display = 'none';
                // Update the histogram for the existing image
                updateChart(data.histogram);


            } else {
                area.style.display = 'block'; // Only show the upload area if there is no image
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }


    // This function will send the image ID to the backend and update the displayed image and histogram
    function applyHistogramEqualization(imageId) {
        const formData = new URLSearchParams();
        formData.append('image_id', imageId);
    
        fetch('/equalize-histogram/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Server responded with a status: ' + response.status);
            }
        })
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                throw new Error('Error in response: ' + JSON.stringify(data));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying histogram equalization: ' + error.message);
        });
    }

    
    // Add event listener to the "Apply Equalization" button
    document.getElementById('apply-equalization-button').addEventListener('click', function() {
        var imageId = uploadedImage.getAttribute('data-image-id');
        console.log('Applying equalization to image ID:', imageId); // Add this line to debug.
        if(imageId) {
            applyHistogramEqualization(imageId);
        } else {
            alert('No image has been uploaded or image ID is missing.');
        }
    });







    // Log Transformation functionality
    document.getElementById('ltcvalue').addEventListener('click', function() {
        var cValue = document.querySelector('.ltinput').value;
        var imageId = uploadedImage.getAttribute('data-image-id');
    
        if(imageId && cValue) {
            applyLogTransformation(imageId, cValue);
        } else {
            alert('Please upload an image and enter a valid C value.');
        }
    });
    
    function applyLogTransformation(imageId, cValue) {
        const formData = new URLSearchParams();
        formData.append('image_id', imageId);
        formData.append('c_value', cValue);
    
        fetch('/apply-log-transformation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Server responded with a status: ' + response.status);
            }
        })
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                updateChart(data.histogram);
            } else {
                throw new Error('Error in response: ' + JSON.stringify(data));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Log Transformation.');
        });
    }


    // Power Law Transformation functionality
    document.getElementById('button-gamma').addEventListener('click', function() {
        var cValue = document.querySelector('.plinputc').value;
        var yValue = document.querySelector('.plinputy').value;
    
        var formData = new URLSearchParams();
        formData.append('c_value', cValue);
        formData.append('y_value', yValue);
    
        fetch('/apply-power-law-transformation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying Power-Law Transformation.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Power-Law Transformation.');
        });
    });



    // Image Negative functionality
    document.getElementById('createnegative').addEventListener('click', function() {
        fetch('/apply-image-negative/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error creating image negative.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error creating image negative.');
        });
    });



    // Convolution Spatial Filtering functionality
    document.getElementById('apply-spatial').addEventListener('click', function() {
        var kernelType = document.querySelector('input[name="kernel"]:checked').id;
    
        var formData = new URLSearchParams();
        formData.append('kernel_type', kernelType);
    
        fetch('/apply-spatial-filter/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying spatial filter.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying spatial filter.');
        });
    });

    
    // Convolution Mean/Average Filtering functionality
    document.getElementById('apply-meanaverage').addEventListener('click', function() {
        fetch('/apply-mean-average-filter/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying Mean/Average filter.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Mean/Average filter.');
        });
    });
    


    // Convolution Median Filtering functionality
    document.getElementById('apply-median').addEventListener('click', function() {
        fetch('/apply-median-filter/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying Median filter.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Median filter.');
        });
    });



    // Nearest Neighbor Interpolation functionality
    document.getElementById('apply-nni').addEventListener('click', function() {
        var scalingFactor = parseInt(document.getElementById('nni').value, 10);

        // Check if scaling factor is within the allowed range
        if (scalingFactor < 10 || scalingFactor > 200) {
            alert('Scaling factor must be between 10% and 200%.');
            return;  // Stop the function if the scaling factor is out of bounds
        }
    
        var formData = new URLSearchParams();
        formData.append('scaling_factor', scalingFactor);
    
        fetch('/apply-nearest-neighbor-interpolation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying Nearest-Neighbor Interpolation.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Nearest-Neighbor Interpolation.');
        });
    });
    


    // Bilinear Interpolation functionality
    document.getElementById('apply-bilinear').addEventListener('click', function() {
        var scalingFactor = document.getElementById('bilinear').value;
    
        // Validate the scaling factor
        if (scalingFactor < 10 || scalingFactor > 200) {
            alert('Scaling factor must be between 10% and 200%.');
            return;
        }
    
        var formData = new URLSearchParams();
        formData.append('scaling_factor', scalingFactor);
    
        fetch('/apply-bilinear-interpolation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
            } else {
                alert('Error applying Bilinear Interpolation.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error applying Bilinear Interpolation.');
        });
    });

    


    // RLE Encoding functionality
    document.getElementById('rlecompress').addEventListener('click', function() {
        fetch('/apply-rle-compression/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Network response was not ok.');
        })
        .then(blob => {
            // Create a link element, use it to download the blob, and remove it
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'compressed_image.txt';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error compressing the image.');
        });
    });

    


    // Huffman Encoding functionality
    document.getElementById('applyhuffman').addEventListener('click', function() {
        fetch('/apply-huffman-coding/', {
            method: 'GET',
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Network response was not ok.');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'huffman_compressed_image.txt';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error compressing the image.');
        });
    });


    // Image Decompression functionality
    function handleDecoding() {
        var decodeOption = document.querySelector('input[name="decodeoption"]:checked').id;
        var fileInput = document.getElementById('codedFile');
    
        if (!fileInput.files.length) {
            alert('Please select a file to upload.');
            return;
        }
    
        var file = fileInput.files[0];
        if (!file.name.endsWith('.txt')) {
            alert('Please upload a .txt file.');
            return;
        }
    
        var formData = new FormData();
        formData.append('decodeoption', decodeOption);
        formData.append('codedFile', file);

        fetch('/decode-and-preview/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                uploadedImage.style.display = 'block';
                
                if ('image_id' in data) {
                    console.log('Image ID:', data.image_id);
                    uploadedImage.setAttribute('data-image-id', data.image_id);
                } else {
                    console.error('Image ID is missing from the response');
                }

                form.style.display = 'none';
                area.style.display = 'none'; // Hide the drag and drop area
                if (!uploadedImage.id) {
                    uploadedImage.id = 'uploaded-image';
                    area.appendChild(uploadedImage);
                }
                // Update the histogram chart with actual data from the backend
                updateChart(data.histogram);
                // // Display the decoded image on the frontend
                // uploadedImage.src = data.url;
                // uploadedImage.style.display = 'block';
                // // Update any other UI elements as necessary
                // form.style.display = 'none';
                // area.style.display = 'none';
            } else {
                alert('Error decoding the file.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error decoding the file.');
        });
    }
    
    document.getElementById('apply-decoding-button').addEventListener('click', handleDecoding);





    // Image Segmentation functionality
    document.getElementById('runsegmentation').addEventListener('click', function() {
        const segmentationType = document.querySelector('input[name="segmentation"]:checked').id;
        const formData = new URLSearchParams();
        formData.append('segmentation_type', segmentationType);
    
        fetch('/apply-segmentation/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
            } else {
                alert('Error running segmentation.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error running segmentation.');
        });
    });
    
    
    
    





    // Revert button functionality
    document.getElementById('revert-button').addEventListener('click', function() {
        fetch('/revert-image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.url) {
                uploadedImage.src = data.url;
                // Update the histogram or any other UI elements as necessary
            } else {
                alert('Error reverting the image.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error reverting the image.');
        });
    });
    




    // Delete image button
    document.getElementById('delete-button').addEventListener('click', function() {
        const imageId = uploadedImage.getAttribute('data-image-id');
    
        if (!imageId) {
            alert('No image selected for deletion.');
            return;
        }
    
        if (!confirm('Are you sure you want to delete this image and all its variants?')) {
            return;
        }
    
        const formData = new URLSearchParams();
        formData.append('image_id', imageId);
    
        fetch('/delete-image/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Image and its variants have been successfully deleted.');
                // Optionally, reset the image display or redirect the user
                uploadedImage.src = ''; // Reset image display
                uploadedImage.removeAttribute('data-image-id'); // Remove image ID attribute

                //form.style.display = 'block';
                //area.style.display = 'block'; // Hide/show the drag and drop area
                //uploadedImage.style.display = 'none';
            } else {
                alert('Error deleting the image. ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('There was an error deleting the image.');
        });
    });
    


    

    // Delete image on page refresh or close
    window.addEventListener('beforeunload', function(event) {
        var imageId = uploadedImage.getAttribute('data-image-id');
        if (imageId) {
            var data = new FormData();
            data.append('image_id', imageId);
            navigator.sendBeacon('/delete-image/', data);
        }
    });


    // Export image functionality
    document.getElementById('pngsave').addEventListener('click', function() {
        downloadImage('png');
    });
    
    document.getElementById('jpgsave').addEventListener('click', function() {
        downloadImage('jpg');
    });
    
    document.getElementById('webpsave').addEventListener('click', function() {
        downloadImage('webp');
    });

    // function downloadImage(format) {
    //     window.location.href = `/download-image/${format}/`;
    // }

    function downloadImage(format) {
        fetch(`/download-image/${format}/`)
            .then(response => response.blob())
            .then(blob => {
                // Create a link element, use it to download the file, and remove it
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `downloaded_image.${format}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            })
            .catch(error => console.error('Download failed:', error));
    }
  


    // Call this function on page load to check for any existing uploaded images
    checkForUploadedImage();
});




document.addEventListener('DOMContentLoaded', function() {
    var beforeAfterButton = document.getElementById('before-after-slider');
    var originalImage = document.getElementById('original-image');
    var sliderContainer = document.getElementById('image-comparison-container');
    var sliderInitialized = false;

    beforeAfterButton.addEventListener('click', function() {
        if (!sliderInitialized) {
            // Fetch the original image URL from the server
            fetch('/get-original-image/')  // Update with your URL
                .then(response => response.json())
                .then(data => {
                    if (data.url) {
                        originalImage.src = data.url;
                        originalImage.style.display = 'block';

                        // Initialize the TwentyTwenty plugin
                        $(sliderContainer).twentytwenty();

                        sliderInitialized = true;
                    } else {
                        console.error('Original image URL not found');
                    }
                })
                .catch(error => console.error('Error fetching original image:', error));
        }
        // No action on subsequent clicks
    });
});





// document.addEventListener('DOMContentLoaded', function() {
//     var beforeAfterButton = document.getElementById('before-after-slider');
//     var originalImage = document.getElementById('original-image');
//     var sliderContainer = document.getElementById('image-comparison-container');
//     var sliderInitialized = false;

//     beforeAfterButton.addEventListener('click', function() {
//         if (!sliderInitialized) {
//             // Fetch the original image URL from the server
//             fetch('/get-original-image/')  // Update with your URL
//                 .then(response => response.json())
//                 .then(data => {
//                     if (data.url) {
//                         originalImage.src = data.url;
//                         originalImage.style.display = 'block';

//                         // Initialize the TwentyTwenty plugin
//                         $(sliderContainer).twentytwenty();

//                         sliderInitialized = true;
//                     } else {
//                         console.error('Original image URL not found');
//                     }
//                 })
//                 .catch(error => console.error('Error fetching original image:', error));
//         } else {
//             // Toggle the visibility of the original image and the slider
//             var isSliderVisible = originalImage.style.display !== 'none';
//             originalImage.style.display = isSliderVisible ? 'none' : 'block';
//             sliderContainer.style.display = isSliderVisible ? 'none' : 'block';
//         }
//     });
// });








$(document).ready(function() {
    
    "use strict";
    $('#apply-equalization-button').click(function() { 
        $('#main-ops-equalization').block({ 
            message: '<div class="spinner-grow text-success" role="status"><span class="sr-only"></span></div>',
            timeout: 500 
        }); 

    }); 

    // $('#blockui-2').click(function() { 
    //     $.blockUI({ 
    //         message: '<div class="spinner-grow text-success" role="status"><span class="sr-only">Loading...</span></div>',
    //         timeout: 2000 
    //     }); 
    // }); 


});



