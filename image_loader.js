window.canvas = document.getElementById('canvas');
window.ctx = canvas.getContext('2d');

// function requires an element: <input type="file" id="imgLoader">
// loads image into window.orig_im, then draws image on variable
// window.canvas. Then captures imgdata as window.im (pure uint8 data)
document.getElementById('imgLoader').onchange = function handleImage(e) {
    var reader = new FileReader();
    reader.onload = function (event) { console.log('going to load image');
        orig_im = new Image();
        orig_im.src = event.target.result;
        orig_im.onload = function () {
            drawImageOntoCanvas(canvas, orig_im);
            window.orig_im = get_canvas_img(canvas);
            window.pix = window.orig_im.data;
        }
    }
    reader.readAsDataURL(e.target.files[0]);
}

function drawImageOntoCanvas(canvas, image) {
    //resizes canvas internally so that full image is displayed. However, the
    //visual size of canvas within browser is not modified.
    canvas.width = image.width;
    canvas.height = image.height;
    ctx = canvas.getContext('2d');
    ctx.drawImage(image, 0, 0);
}

function get_canvas_img(canvas) {
    // assumes that canvas.width & canvas.height have been set to dimensions of 
    // loaded image. Will return the full image data
    ctx = canvas.getContext('2d');
    w = canvas.width;
    h = canvas.height;
    return ctx.getImageData(0, 0, w, h);
} 

function new_image(im) {
    // create blank image with same dimensions as im (or window.orig_im if no
    // image passed)
    if (im == undefined) {
        im = window.orig_im
    }
    return window.ctx.createImageData(im);
}

function copy_imgdata(src, dest) {
    // copy imgdata from src to dest by iterating over all indices
    for (i=0; i < src.length; i++) {
        dest[i] = src[i];
    }
}

function copy_image(img) {
    copy = new_image(img);
    copy_imgdata(img.data, copy.data);
    return copy;
}

function strip_alpha_channel(img) {
    // sets an image's alpha channel to opaque
    var opaque = 255;
    var alpha_index = 3;
    var rgba = 4;  // number of colors in image
    while (alpha_index < img.data.length) {
        img.data[alpha_index] = opaque;
        alpha_index += rgba;
    }
}

function to_greyscale(img) {
    
}
