document.getElementById('imgLoader').onchange = function handleImage(e) {
    /*function requires an element: <input type="file" id="imgLoader">
     loads image into window.orig_im, draws image on window.canvas. Then
     captures imgdata as window.pix (pure uint8 data)
     */
    var reader = new FileReader();
    reader.onload = function (event) { console.log('going to load image');
        orig_im = new Image();
        orig_im.onload = function () {
            var orig_canv = document.getElementById('canvas');
            CanvImg.draw_raw_img_on_canvas(orig_canv, orig_im);
            first_img = CanvImg.get_canvas_img(orig_canv);
            step1_greyscale(first_img);
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

function step2_blur(grey_img) {
    img_tuple = CanvImg.create_arrays_from_image(grey_img);
    grey_array = img_tuple[0];
    blur_array = Canny.convolve(grey_array, Canny.KERNEL.gaussian, grey_img);
    var blur_img = CanvImg.create_greyscale_image_from_array(grey_img, blur_array);
    var canv_blur = document.getElementById('canvas-3');
    CanvImg.draw_img_on_canvas(canv_blur, blur_img);
    setTimeout(function() {step3_edge_detect_x(blur_img, blur_array);}, 10);
}

function step3_edge_detect_x(blur_img, blur_array) {
    xedge = Canny.convolve(blur_array, Canny.KERNEL.sobel_x, blur_img);
    edge_x = CanvImg.create_greyscale_image_from_array(blur_img, xedge);
    // red color is positive x edges, cyan is negative x edges
    var canv_xedge = document.getElementById('canvas-edge-x');
    CanvImg.draw_img_on_canvas(canv_xedge, edge_x);
    setTimeout(function(){step4_edge_detect_y(blur_img, blur_array);}, 10);
}

function step4_edge_detect_y(blur_img, blur_array) {
    yedge = Canny.convolve(blur_array, Canny.KERNEL.sobel_y, blur_img);
    edge_y = CanvImg.create_greyscale_image_from_array(blur_img, yedge);
    // yellow is positive y edges, blue is negative y edges
    var canv_yedge = document.getElementById('canvas-edge-y');
    CanvImg.draw_img_on_canvas(canv_yedge, edge_y);
    setTimeout(function(){step5_combine_edges(blur_img, blur_array);}, 10);
}

function step5_combine_edges(blur_img, blur_array) {
    var canv_edge = document.getElementById('canvas-edge');
    var edge_mag = CanvImg.average_2_images(edge_x, edge_y);
    CanvImg.draw_img_on_canvas(canv_edge, edge_mag);
    edge_mag = Canny.calculate_edge_magnitude(window.xedge, window.yedge);
}
