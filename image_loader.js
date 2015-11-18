"use strict";

window.canvas = document.getElementById('canvas');
window.ctx = canvas.getContext('2d');
window.grey_canvas = document.getElementById('canvas-grey');

document.getElementById('imgLoader').onchange = function handleImage(e) {
    /*function requires an element: <input type="file" id="imgLoader">
     loads image into window.orig_im, draws image on window.canvas. Then
     captures imgdata as window.pix (pure uint8 data)
     */
    var reader = new FileReader();
    reader.onload = function (event) { console.log('going to load image');
        orig_im = new Image();
        orig_im.onload = function () {
            // copy from auto_load_image once finished creating    
        }
        orig_im.src = event.target.result;
    }
    reader.readAsDataURL(e.target.files[0]);
}

auto_load_image();  // FOR TESTING ONLY (have to run python2 -m SimpleHTTPServer to activate

function auto_load_image() {
    /*auto-loads image from file to assist in coding 
     */
    var orig_im = new Image();
    orig_im.onload = function() {
        draw_raw_img_on_canvas(window.canvas, orig_im);
        window.im = orig_im;
        window.orig_im = get_canvas_img(canvas);
        window.pix = window.orig_im.data;
        step1_greyscale(window.orig_im);
    }
    orig_im.src = "car.jpg";
}

function step1_greyscale(img) {
    window.grey = get_greyscale(img);
    draw_img_on_canvas(window.grey_canvas, grey);
    step2_blur(grey);
}

function step2_blur(img) {
    var blurred = convolve(img, KERNEL.gaussian);
    draw_img_on_canvas(document.getElementById('canvas-3'), blurred);
    step3_edge_detect_xy(blurred);
}

function step3_edge_detect_xy(img) {
    var no_normalize = 1;  // sobel kernel's auto-normalize
    var edge_x = convolve(img, KERNEL.sobel_x, no_normalize);
    var edge_y = convolve(img, KERNEL.sobel_y, no_normalize);
    draw_img_on_canvas(document.getElementById('canvas-edge-x'), edge_x);
    draw_img_on_canvas(document.getElementById('canvas-edge-y'), edge_y);
}

function draw_img_on_canvas(canvas, image) {
    /*resizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not modified.
     use this fxn to draw any image that you've modified from the original.
     */
    canvas.width = image.width;
    canvas.height = image.height;
    var ctx = canvas.getContext('2d');
    ctx.putImageData(image, 0, 0);
}

function draw_raw_img_on_canvas(canvas, raw_image) {
    /*This is used only once; to draw the img after being loaded from file.
     sizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not modified.
     */
    canvas.width = raw_image.width;
    canvas.height = raw_image.height;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(raw_image, 0, 0);

}

function get_canvas_img(canvas) {
    /*assumes that canvas.width & canvas.height have been set to dimensions of 
    loaded image. Will return the full image data
     */
    var ctx = canvas.getContext('2d');
    var w = canvas.width,
        h = canvas.height;
    return ctx.getImageData(0, 0, w, h);
} 

function new_image(im) {
    /*create blank image with same dimensions as im (or window.orig_im if no
     image passed)
     */
    if (im == undefined) {
        var im = window.orig_im
    }
    return window.ctx.createImageData(im);
}

function copy_imgdata(src, dest) {
    // copy imgdata from src to dest by iterating over all indices
    var i;
    for (i=0; i < src.length; i++) {
        dest[i] = src[i];
    }
}

function copy_image(img) {
    var copy = new_image(img);
    copy_imgdata(img.data, copy.data);
    return copy;
}

window.NUM_COLORS = 4;

window.KERNEL = {

    'blur': [1, 1, 1,
             1, 1, 1,
             1, 1, 1],

    'sobel_y': [-1, -2, -1,
                 0,  0,  0,
                +1, +2, +1],

    'sobel_x': [-1, 0, +1, 
                -2, 0, +2,
                -1, 0, +1],

    'sobel_y_reverse': [+1, +2, +1,
                         0,  0,  0,
                        -1, -2, -1],

    'sobel_x_reverse': [+1, 0, -1, 
                        +2, 0, -2,
                        +1, 0, -1],

    'gaussian': [2,  4,  5,  4, 2,
                 4,  9, 12,  9, 4,
                 5, 12, 15, 12, 5,
                 2,  4,  5,  4, 2,
                 4,  9, 12,  9, 4],
};

function convolve(img, kernel, normalize) {
    /* convolve a kernel with an image, returning a new image with the same
     * dimensions post-convolution. Auto-normalizes values so that image is not
     * washed-out / faded. Overall resulting img should have ~ same luminosity
     * as original.
     */
    var new_img = copy_image(img),
        ksqrt = Math.sqrt(kernel.length);
    if ((Math.round(ksqrt) != ksqrt) || (ksqrt % 2 == 0)) {
        console.log('kernel must be square, with odd-length sides like 3x3, 5x5');
    }
    if (normalize === undefined) {
        normalize = 0;
        kernel.forEach(function(num) {
            normalize += num;
        });
    }
    // neighbors == # depth of neighbors around kernel center. 3x3 = 1 neighbor
    var neighbors = (ksqrt - 1) / 2,
        k,
        x, y,
        nx, ny,
        p, pixel;
    for (x = 0; x < img.width; x++) {
        for (y = 0; y < img.height; y++) {
            pixel = 0;
            k = -1;  // index of kernel
            for (ny = -neighbors; ny <= neighbors; ny++) {
                for (nx = -neighbors; nx <= neighbors; nx++) {
                    p = get_pixel(img, x + nx, y + ny) || get_pixel(img, x, y);
                    pixel += p * kernel[++k];  //weight pixel value
                }
            }
            pixel /= normalize;  //prevents over/undersaturation of img
            set_pixel(new_img, x, y, pixel);
        }
    }
    return new_img;
}

function get_pixel(img, x, y) {
    /* this assumes that img is now greyscale. Return Red component of pixel at
     * coordinates (x,y)
     */
    x *= NUM_COLORS;
    y *= NUM_COLORS * img.width;
    return img.data[x + y];
}

function set_pixel(img, x, y, luminosity) {
    // this assumes that img is now greyscale. Sets Red, Green, & Blue
    // components of pixel at coordinates (x,y) to value
    x *= NUM_COLORS;
    y *= NUM_COLORS * img.width;
    img.data[x + y] = value;
    img.data[x + 1 + y] = value;
    img.data[x + 2 + y] = value;
}

function set_pixel_color(img, x, y, color_indices, luminosity) {
    /* set a specific color-indices @ x, y to given luminosity. So [1], 255
     * would set the pixel at x,y to rgb values: (0, 255, 0).
     * [0,1], 128 would set the rbg values @x,y to (128, 128, 0)
     */
    x *= NUM_COLORS;
    y *= NUM_COLORS * img.width;
    color_indices.forEach(function(i) {
        if ((i == 0) || (i == 1) || (i ==2)) {
            img.data[x + y + i] = luminosity;
        } else {
            console.log('error: set_pixel_color accessed color outside rgb');
        }
    });
}

function strip_alpha_channel(img) {
    // sets an image's alpha channel to opaque
    var opaque = 255,
        alpha_index = 3,
        num_colors = 4,  //rgba (4 colors in image)
        i;
    for (i = alpha_index; i < img.data.length; i += num_colors) {
        img.data[i] = opaque;
    }
}

function get_greyscale(img) {
    // return a grayscaled copy of img
    var img = copy_image(img),
        alpha_index = 3,
        num_colors = 4,
        data = img.data,
        scaling = [0.299, 0.587, 0.114],
        greyscale,
        r, g, b,
        i;
    for (i = 0; i < data.length; i += num_colors) {
         r = data[i + 0];
         g = data[i + 1];
         b = data[i + 2];
         greyscale = r * scaling[0] + g * scaling[1] + b * scaling[2];
         data[i + 0] = greyscale;
         data[i + 1] = greyscale;
         data[i + 2] = greyscale;
    }
    return img;
}
