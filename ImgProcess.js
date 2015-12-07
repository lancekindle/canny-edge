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
            first_img = CanvImg.get_canvas_image(orig_canv);
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
        first_img = CanvImg.get_canvas_image(orig_canv);
        step1_greyscale(first_img);
    }
    orig_im.src = "car.jpg";
}

function step1_greyscale(img) {
    var grey_img = CanvImg.get_greyscale(img);
    var canv_grey = document.getElementById('canvas-grey');
    CanvImg.push_image_to_canvas(canv_grey, grey_img);

    //create a "steps" object to hold onto all variables made in each step.
    //step1 will hold variables created in step1, and can be accessed as
    //steps[1]
    window.steps = {};
    var step1 = {
        grey_img: grey_img,
        ref_img: img
    };
    steps[1] = step1;
    setTimeout(function() {step2_blur(steps);}, 10);
}

function step2_blur(steps) {
    var grey_img = steps[1].grey_img;
    var img_tuple = CanvImg.create_arrays_from_image(grey_img);
    var grey = img_tuple[0];
    var blur  = Canny.convolve(grey, Canny.KERNEL.gaussian, grey_img);
    var blur_img = CanvImg.create_greyscale_image(grey_img, blur);
    var canv_blur = document.getElementById('canvas-3');
    CanvImg.push_image_to_canvas(canv_blur, blur_img);
    var blank_img = CanvImg.create_greyscale_image(grey_img, new Array(grey.length));

    var step2 = {
        grey: grey,
        blur: blur,
        blur_img: blur_img,
        blank_img: blank_img
    };
    steps[2] = step2;
    setTimeout(function() {step3_edge_detect_x(steps);}, 10);
}

function step3_edge_detect_x(steps) {
    var blur = steps[2].blur,
        blur_img = steps[2].blur_img;
    var edge_x = Canny.convolve(blur, Canny.KERNEL.sobel_x, blur_img);
    var edge_x_img = CanvImg.create_greyscale_image(blur_img, edge_x);
    // red color is positive x edges, cyan is negative x edges
    var canv_xedge = document.getElementById('canvas-edge-x');
    CanvImg.push_image_to_canvas(canv_xedge, edge_x_img);

    var step3 = {
        edge_x: edge_x,
        edge_x_img: edge_x_img
    };
    steps[3] = step3;
    setTimeout(function(){step3_edge_detect_y(steps);}, 10);
}

function step3_edge_detect_y(steps) {
    var blur_img = steps[2].blur_img,
        blur = steps[2].blur;
    var edge_y = Canny.convolve(blur, Canny.KERNEL.sobel_y, blur_img);
    var edge_y_img = CanvImg.create_greyscale_image(blur_img, edge_y);
    // yellow is positive y edges, blue is negative y edges
    var canv_yedge = document.getElementById('canvas-edge-y');
    CanvImg.push_image_to_canvas(canv_yedge, edge_y_img);

    steps[3].edge_y = edge_y;
    steps[3].edge_y_img = edge_y_img;
    setTimeout(function(){step4_calculate_edge_magnitude(steps);}, 10);
}

function step4_calculate_edge_magnitude(steps) {
    var blur_img = steps[2].blur_img,
        edge_x_img = steps[3].edge_x_img,
        edge_y_img = steps[3].edge_y_img,
        edge_x = steps[3].edge_x,
        edge_y = steps[3].edge_y;
    var canv_edge = document.getElementById('canvas-edge');
    var edge_mag_img = CanvImg.average_2_images(edge_x_img, edge_y_img);
    //CanvImg.push_image_to_canvas(canv_edge, edge_mag);
    var edge_mag = Canny.calculate_edge_magnitude(edge_x, edge_y);
    edge_mag = Canny.scale_array_0_to_255(edge_mag);
    var edge_mag_img = CanvImg.create_greyscale_image(blur_img, edge_mag);
    CanvImg.push_image_to_canvas(canv_edge, edge_mag_img);

    var step4 = {
        edge_mag: edge_mag,
        edge_mag_img: edge_mag_img
    };
    steps[4] = step4;
    setTimeout(function(){step5_color_img_according_to_angles(steps);}, 10);
}

function step5_color_img_according_to_angles(steps) {
    var edge_x = steps[3].edge_x,
        edge_y = steps[3].edge_y,
        edge_mag_img = steps[4].edge_mag_img,
        edge_mag = steps[4].edge_mag;
    var edge_angle = Canny.calculate_edge_angle(edge_x, edge_y);
    var angle_rgb = Colorwheel.rgb_from_angle(edge_angle);
    var r = angle_rgb[0],
        g = angle_rgb[1],
        b = angle_rgb[2];
    var bright_img = CanvImg.create_image_from_arrays(edge_mag_img, r, g, b);
    CanvImg.push_image_to_canvas(bright_color_canv, bright_img);
    var scaled_angle_rgb = Colorwheel.scale_rgb_with_intensity(angle_rgb, edge_mag);
    r = scaled_angle_rgb[0],
    g = scaled_angle_rgb[1],
    b = scaled_angle_rgb[2];
    var angle_colored_img = CanvImg.create_image_from_arrays(edge_mag_img, r, g, b);
    CanvImg.push_image_to_canvas(angle_color_canv, angle_colored_img);

    var step5 = {
        angle_rgb: angle_rgb,
        scaled_angle_rgb: scaled_angle_rgb,
        edge_angle: edge_angle,
        bright_img: bright_img
    };
    steps[5] = step5;
    setTimeout(function(){step6_split_img_into_four_bidirectionals(steps);}, 10);
}

function step6_split_img_into_four_bidirectionals(steps) {
    var edge_angle = steps[5].edge_angle,
        edge_mag = steps[4].edge_mag,
        angle_rgb = steps[5].angle_rgb,
        ref_img = steps[1].ref_img;
    var splitter = Canny.get_bidirectional_splitter_from_angle(edge_angle);
    // split_mag is the image from which we will perform actual calculations
    var split_mag = Canny.split_array_into_four_bidirections(edge_mag, splitter);
    var r = angle_rgb[0],
        g = angle_rgb[1],
        b = angle_rgb[2];  // these are correctly scaled rgb-values
    // split r, g, b arrays into four and recombine r,g, &b for each
    // bidirection to display for user
    var a = new Array(r.length);
    a.fill(CanvImg.OPAQUE);
    var alpha_split = Canny.split_array_into_four_bidirections(a, splitter);
    // I use the full-colored angle image, and adjust the alpha on each image
    // according to it's gradient strength. This makes the image look perfect
    // if cast on a black background
    for (var i = 0; i < Canny.BIDIRECTIONS.length; i++) {
        var direction = Canny.BIDIRECTIONS[i];
        var mag = split_mag[direction];
        var bi_color_img = CanvImg.create_image_from_arrays(ref_img, r, g, b, mag);
        var bi_canv = document.getElementById(direction + '_split_angle_canv');
        CanvImg.push_image_to_canvas(bi_canv, bi_color_img);
    }

    step6 = {
        alpha_split: alpha_split,
        split_mag: split_mag,
        splitter: splitter
    };
    steps[6] = step6;
    setTimeout(function(){step7_thin_split_images(steps);}, 10);
}

function step7_thin_split_images(steps) {
    var split_mag = steps[6].split_mag,
        angle_rgb = steps[5].angle_rgb,
        ref_img = steps[1].ref_img;
    var r = angle_rgb[0],
        g = angle_rgb[1],
        b = angle_rgb[2];
    var thin_split_mag = Canny.apply_thinning_to_split_array(ref_img, split_mag);
    for (var i = 0; i < Canny.BIDIRECTIONS.length; i++) {
        var direction = Canny.BIDIRECTIONS[i];
        var mag = thin_split_mag[direction];
        var bi_color_img = CanvImg.create_image_from_arrays(ref_img, r, g, b, mag);
        var bi_canv = document.getElementById(direction + '_thin_split_angle_canv');
        CanvImg.push_image_to_canvas(bi_canv, bi_color_img);
    }
    var thin_mag = Canny.combine_split_arrays(thin_split_mag);
    var thin_mag_img = CanvImg.create_greyscale_image(ref_img, thin_mag);
    var full_mag_canv = document.getElementById('full_magnitude_thin_canv');
    CanvImg.push_image_to_canvas(full_mag_canv, thin_mag_img);
    
    step7 = {
        thin_split_mag: thin_split_mag,
        thin_mag: thin_mag
    }
    steps[7] = step7;
    setTimeout(function(){step8_threshold_thin_image(steps);}, 10);
}

function step8_threshold_thin_image(steps, strong, weak) {
    if (strong === undefined)
        strong = 63;
    if (weak === undefined)
        weak = strong - 30;
    var thin_mag = steps[7].thin_mag,
        ref_img = steps[1].ref_img;
    var strong_mag = CanvImg.threshold_array(thin_mag, strong);
    var weak_mag = CanvImg.threshold_array(thin_mag, weak);
    // strong pixels are white, weak pixels are magenta (purple)
    var color_thresh_img = CanvImg.create_image_from_arrays(ref_img, weak_mag, strong_mag, weak_mag);
    CanvImg.push_image_to_canvas(strong_threshold_canv, color_thresh_img);

    step8 = {
        strong_mag: strong_mag,
        weak_mag: weak_mag
    }
    steps[8] = step8;
    setTimeout(function(){step9_edge_tracking(steps);}, 10);
}

function step9_edge_tracking(steps) {
    var ref_img = steps[1].ref_img,
        strong_mag = steps[8].strong_mag,
        weak_mag = steps[8].weak_mag;
    var tracked_edges = CanvImg.apply_pixel_tracking(ref_img, strong_mag, weak_mag);
    var tracked_edges_img = CanvImg.create_greyscale_image(ref_img, tracked_edges);
    CanvImg.push_image_to_canvas(tracked_edges_canv, tracked_edges_img);
}

