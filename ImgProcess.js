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
    setTimeout(function() {step2_blur(grey);}, 10);
}

function step2_blur(img) {
    var blurred = convolve(img, KERNEL.gaussian);
    draw_img_on_canvas(document.getElementById('canvas-3'), blurred);
    setTimeout(function() {step3_edge_detect_x(blurred);}, 10);
}

function step3_edge_detect_x(img) {
    var no_normalize = 1;  // sobel kernel's auto-normalize
    var edge_x_pos = convolve(img, KERNEL.sobel_x, no_normalize);
    var edge_x_neg = convolve(img, KERNEL.sobel_x_reverse, no_normalize);
    var edge_x = colorfly_combine_3_images(edge_x_pos, edge_x_neg, undefined);
    // red color is positive x edges, green is negative x edges
    draw_img_on_canvas(document.getElementById('canvas-edge-x'), edge_x);
    setTimeout(function(){step4_edge_detect_y(img);}, 10);
}

function step4_edge_detect_y(img) {
    var no_normalize = 1;
    var edge_y_pos = convolve(img, KERNEL.sobel_y, no_normalize);
    var edge_y_neg = convolve(img, KERNEL.sobel_y_reverse, no_normalize);
    var edge_y = colorfly_combine_3_images(edge_y_pos, edge_y_pos, edge_y_neg);
    // yellow is positive y edges, blue is negative y edges
    draw_img_on_canvas(document.getElementById('canvas-edge-y'), edge_y);
}