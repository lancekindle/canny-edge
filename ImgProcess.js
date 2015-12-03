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
    setTimeout(function(){step5_calculate_edge_magnitude(blur_img, blur_array);}, 10);
}

function step5_calculate_edge_magnitude(blur_img, blur_array) {
    var canv_edge = document.getElementById('canvas-edge');
    var edge_mag = CanvImg.average_2_images(edge_x, edge_y);
    //CanvImg.draw_img_on_canvas(canv_edge, edge_mag);
    mag_edge = Canny.calculate_edge_magnitude(window.xedge, window.yedge);
    mag_edge = Canny.scale_array_0_to_255(mag_edge);
    edge_mag_img = CanvImg.create_greyscale_image_from_array(blur_img, mag_edge);
    CanvImg.draw_img_on_canvas(canv_edge, edge_mag_img);
    step6_color_img_according_to_angles(edge_mag_img, mag_edge);
}

function step6_color_img_according_to_angles(mag_img, mag_array) {
    angle_edge = Canny.calculate_edge_angle(window.xedge, window.yedge);
    angle_rgb = Colorwheel.rgb_from_angle(angle_edge);
    var r = angle_rgb[0],
        g = angle_rgb[1],
        b = angle_rgb[2];
    bright_img = CanvImg.create_image_from_arrays(mag_img, r, g, b);
    CanvImg.draw_img_on_canvas(bright_color_canv, bright_img);
    // change in-place r, g, b arrays
    Colorwheel.scale_rgb_with_intensity(angle_rgb, mag_edge);
    angle_colored_img = CanvImg.create_image_from_arrays(mag_img, r, g, b);
    CanvImg.draw_img_on_canvas(angle_color_canv, angle_colored_img);
    step7_split_img_into_four_bidirectionals(mag_img, mag_array);
}

function step7_split_img_into_four_bidirectionals(mag_img, mag_array) {
    splitter = Canny.get_bidirectional_splitter_from_angle(angle_edge);
    // split_mag is the image from which we will perform actual calculations
    split_mag = Canny.split_array_into_four_bidirections(mag_array, splitter);
    var r = angle_rgb[0],
        g = angle_rgb[1],
        b = angle_rgb[2];  // these are correctly scaled rgb-values
    // split r, g, b arrays into four and recombine r,g, &b for each
    // bidirection to display for user
    red_split = Canny.split_array_into_four_bidirections(r, splitter);
    green_split = Canny.split_array_into_four_bidirections(g, splitter);
    blue_split = Canny.split_array_into_four_bidirections(b, splitter);
    for (var i = 0; i < Canny.BIDIRECTIONS.length; i++) {
        var direction = Canny.BIDIRECTIONS[i];
        r = red_split[direction];
        g = green_split[direction];
        b = blue_split[direction];
        var bi_color_img = CanvImg.create_image_from_arrays(mag_img, r, g, b);
        var bi_canv = document.getElementById(direction + '_split_angle_canv');
        CanvImg.draw_img_on_canvas(bi_canv, bi_color_img);
    }
}
