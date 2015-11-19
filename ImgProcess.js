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
        var orig_canv = document.getElementById('canvas');
        CanvImg.draw_raw_img_on_canvas(orig_canv, orig_im);
        first_img = CanvImg.get_canvas_img(orig_canv);
        step1_greyscale(first_img);
    }
    orig_im.src = "car.jpg";
}

function step1_greyscale(img) {
    var grey = CanvImg.get_greyscale(img);
    var canv_grey = document.getElementById('canvas-grey');
    CanvImg.draw_img_on_canvas(canv_grey, grey);
    setTimeout(function() {step2_blur(grey);}, 10);
}

function step2_blur(img) {
    var blurred = CanvImg.convolve(img, CanvImg.KERNEL.gaussian);
    var canv_blur = document.getElementById('canvas-3');
    CanvImg.draw_img_on_canvas(canv_blur, blurred);
    setTimeout(function() {step3_edge_detect_x(blurred);}, 10);
}

function step3_edge_detect_x(img) {
    var no_normalize = 1;  // sobel kernel's auto-normalize
    var edge_x_pos = CanvImg.convolve(img, CanvImg.KERNEL.sobel_x, no_normalize);
    var edge_x_neg = CanvImg.convolve(img, CanvImg.KERNEL.sobel_x_reverse, no_normalize);
    // red color is positive x edges, cyan is negative x edges
    var edge_x = CanvImg.colorfly_combine_3_images(edge_x_pos, edge_x_neg, edge_x_neg);
    var canv_xedge = document.getElementById('canvas-edge-x');
    CanvImg.draw_img_on_canvas(canv_xedge, edge_x);
    setTimeout(function(){step4_edge_detect_y(img, edge_x);}, 10);
}

function step4_edge_detect_y(img, edge_x) {
    var no_normalize = 1;
    var edge_y_pos = CanvImg.convolve(img, CanvImg.KERNEL.sobel_y, no_normalize);
    var edge_y_neg = CanvImg.convolve(img, CanvImg.KERNEL.sobel_y_reverse, no_normalize);
    // yellow is positive y edges, blue is negative y edges
    var edge_y = CanvImg.colorfly_combine_3_images(edge_y_pos, edge_y_pos, edge_y_neg);
    var canv_yedge = document.getElementById('canvas-edge-y');
    CanvImg.draw_img_on_canvas(canv_yedge, edge_y);
    setTimeout(function(){step5_combine_edges(edge_x, edge_y);}, 10);
}

function step5_combine_edges(edge_x, edge_y) {
    var canv_edge = document.getElementById('canvas-edge');
    var edge_mag = CanvImg.average_2_images(edge_x, edge_y);
    CanvImg.draw_img_on_canvas(canv_edge, edge_mag);
}
