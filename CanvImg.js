window.CanvImg = {};

/* call this function immediately. Attaches all the fxns below to CanvImg
 * object. Very similar to how RequireJS runs, but this emulates it closely
 * without requiring the library.
 * This library iterates on, and returns images / arrays whose array represent
 * rows of pixels, one below the other. (any algorithm in here should either
 * iterate over full length with just a single index, or using two for loops,
 * starting with y, then x.
 */
(function(){
"use strict";

CanvImg.NUM_COLORS = 4;
CanvImg.ALPHA = 3;
CanvImg.BLANK = 0;
CanvImg.OPAQUE = 255;

//create, but do not add canvas to document. Keep it for creating a new image.
CanvImg._CANVAS = document.createElement('canvas');

CanvImg.new_image = function(im) {
    //create blank image with same dimensions as im
    var ctx = CanvImg._CANVAS.getContext('2d');
    var new_img = ctx.createImageData(im);
    return new_img;
}

CanvImg.draw_raw_img_on_canvas = function(canvas, raw_image) {
    /*This is used only once; to draw the img loaded from file. It
     sizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not changed.
     */
    canvas.width = raw_image.width;
    canvas.height = raw_image.height;
    var ctx = canvas.getContext('2d');
    ctx.drawImage(raw_image, 0, 0);

}

CanvImg.draw_img_on_canvas = function(canvas, image) {
    /*resizes canvas internally so that full image is displayed. However, the
     visual size of canvas within browser is not modified.
     use this fxn to draw any image that you've modified from the original.
     */
    canvas.width = image.width;
    canvas.height = image.height;
    var ctx = canvas.getContext('2d');
    ctx.putImageData(image, 0, 0);
}

CanvImg.get_canvas_img = function(canvas) {
    /*assumes that canvas.width & canvas.height have been set to dimensions of 
    loaded image. Will return the full image data
     */
    var ctx = canvas.getContext('2d');
    var w = canvas.width,
        h = canvas.height;
    return ctx.getImageData(0, 0, w, h);
}

CanvImg.copy_image = function(img) {
    var copy = CanvImg.new_image(img);
    CanvImg.copy_imgdata(img.data, copy.data);
    return copy;
}

CanvImg.copy_imgdata = function(src, dest) {
    // copy imgdata from src to dest by iterating over all indices
    var i;
    for (i=0; i < src.length; i++) {
        dest[i] = src[i];
    }
}

CanvImg.get_pixel = function(img, x, y) {
    /* this assumes that img is now greyscale. Return Red component of pixel at
     * coordinates (x,y)
     */
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    return img.data[x + y];
}

CanvImg.set_pixel = function(img, x, y, value) {
    // this assumes that img is now greyscale. Sets Red, Green, & Blue
    // components of pixel at coordinates (x,y) to value
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    img.data[x + y] = value;
    img.data[x + 1 + y] = value;
    img.data[x + 2 + y] = value;
}

CanvImg.average_2_images = function(im1, im2) {
    /*average two images together into one image
     */
    var im = CanvImg.new_image(im1);
    var d1 = im1.data,
        d2 = im2.data,
        data = im.data;
    for (var i = 0; i < data.length; i++) {
        data[i] = (d1[i] + d2[i]) / 2;
    }
    return im;
}

CanvImg.create_alpha_mask = function(array) {
    //given an array, generate a alpha mask array. It's values are all
    //CanvImg.BLANK (0) where array has a 0-value. Where array has any other
    //value, the mask array will have a value of CanvImg.OPAQUE (255)
    var len = array.length,
        mask = new Array(len);
    mask.fill(CanvImg.BLANK);
    for (var i = 0; i < len; i++) {
        if (array[i] != 0) {
            mask[i] = CanvImg.OPAQUE;
        }
    }
    return mask;
}

CanvImg.shift_img_array = function(ref_im, array, shift_x, shift_y, fill) {
    /* using an image as reference, insert and remove values in an array so
     * that it's image is shifted by x, y. When inserting values, use
     * the fill parameter, which defaults to CanvImg.BLANK (0).
     */
    if (fill === undefined) {
        fill = CanvImg.BLANK;
    }
    var moved = array.slice(0);  // clones array
    var width = ref_im.width,
        height = ref_im.height;
    // shift positive x direction
    // shifts all values over by one, then replaces values of first column with
    // fill-value.
    for (var x = 0; x < shift_x; x++) {
        moved.pop();
        moved.unshift(fill);
        for (var y = 1; y < height; y++) {
            moved[y * width] = fill;
        }
    }
    // shift negative x direction
    // sets first column values to fill, then shifts image 1 to left, causing
    // all first column values to move to last column. Finally add fill value
    // to last pixel of image
    for (var x = 0; x > shift_x; x--) {
        for (var y = 0; y < height; y++) {
            moved[y * width] = fill;
        }
        moved.shift();
        moved.push(fill);
    }
    // shift positive y direction
    // add one row of fill-values to start of array, pop() one row from end.
    for (var y = 0; y < shift_y; y++) {
        for (var x = 0; x < width; x++) {
            moved.unshift(fill);
            moved.pop();
        }
    }
    //shift negative y direction
    //push one row of fill-values to end of array, remove first row in array.
    for (var y = 0; y > shift_y; y--) {
        for (var x = 0; x < width; x++) {
            moved.shift();
            moved.push(fill);
        }
    }
    return moved;
}

CanvImg.create_image_from_arrays = function(ref_im, r, g, b, a) {
    /* combine 1-4 arrays into an image. The arrays represent, r, g, b, & a in
     * that order.
     * First Argument must be an image that has target height and width. Any
     * array not defined will be assumed value of 0 (except Alpha, which
     * assumes default opaque value)
     */
    if (r === undefined) {
        r = new Array(ref_im.data.length);
        r.fill(0);
    }
    if (g === undefined) {
        g = new Array(ref_im.data.length);
        g.fill(0);
    }
    if (b === undefined) {
        b = new Array(ref_im.data.length);
        b.fill(0);
    }
    if (a === undefined) {
        a = new Array(ref_im.data.length);
        a.fill(CanvImg.OPAQUE);
    }
    var im = CanvImg.new_image(ref_im),
        data = im.data,
        k = -1;
    for (var i = 0; i < data.length; i += CanvImg.NUM_COLORS) {
        k++;
        data[i] = r[k];
        data[i + 1] = g[k];
        data[i + 2] = b[k];
        data[i + 3] = a[k];
    }
    return im;
}

CanvImg.create_greyscale_image_from_array = function(ref_im, array) {
    /* create image from single array. Value from array will be copied to all 3
     * colors: red, green, and blue. Alpha is assumed opaque.
     * Argument must be an image that has target height and width. Any
     * array not defined will be assumed value of 0.
     */
    var im = CanvImg.new_image(ref_im);
    var color,
        data = im.data,
        k = -1;
    for (var i = 0; i < data.length; i += CanvImg.NUM_COLORS) {
        color = array[++k];
        data[i] = color;
        data[i + 1] = color;
        data[i + 2] = color;
        data[i + 3] = CanvImg.OPAQUE;
    }
    return im;
}

CanvImg.create_arrays_from_image = function(im) {
    /* given an image, split into 4 arrays representing r, g, b, & a in that
     * order. Accepting the returned arrays will look like:
     * data = CanvImg.create_arrays_from_image(im);
     * r = data[0];
     * g = data[1];
     * b = data[2];
     * a = data[3];
     */
    var r = [],
        g = [],
        b = [],
        a = [];
    for (var i = 0; i < im.data.length; i += CanvImg.NUM_COLORS) {
        r.push(im.data[i]);
        g.push(im.data[i + 1]);
        b.push(im.data[i + 2]);
        a.push(im.data[i + 3]);
    }
    var colors = {
        red: r,
        0: r,
        green:  g,
        1: g,
        blue: b,
        2: b,
        alpha: a,
        3: a,
    };
    return colors;
}

CanvImg.colorfly_combine_3_images = function(r, g, b) {
    /* combine 3 images together, using each image as a basis for colors r,g,b.
     * first image passed in will provide only red colors, second image provide
     * green colors, third image provides blue colors. It is assumed that the
     * passed in images are greyscale. If you pass in undefined as one of the
     * images, the corresponding color will not appear in the image.
     */
    var im;
    // create im from one of the undefined r, g, or b images
    if (r !== undefined) {
        im = CanvImg.new_image(r);
    } else if (g !== undefined) {
        im = CanvImg.new_image(g);
    } else {
        im = CanvImg.new_image(b);
    }
    CanvImg.strip_alpha_channel(im);
    // if any of the r, g, or b images are undefined, initialize them as an img
    if (r === undefined)
        r = CanvImg.new_image(im);
    if (g === undefined)
        g = CanvImg.new_image(im);
    if (b === undefined)
        b = CanvImg.new_image(im);
    var pixel;
    for (var i = 0; i < im.data.length; i += CanvImg.NUM_COLORS) {
        if (r === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = r.data[i];
        }
        im.data[i] = pixel;
        if (g === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = g.data[i + 1];
        }
        im.data[i + 1] = pixel;
        if (b === undefined) {
            pixel = CanvImg.BLANK;
        } else {
            pixel = b.data[i + 2];
        }
        im.data[i + 2] = pixel;
    }
    return im;
}

CanvImg.set_pixel_color = function(img, x, y, color_indices, luminosity) {
    /* set a specific color-indices @ x, y to given luminosity. So [1], 255
     * would set the pixel at x,y to rgb values: (0, 255, 0).
     * [0,1], 128 would set the rbg values @x,y to (128, 128, 0)
     */
    x *= CanvImg.NUM_COLORS;
    y *= CanvImg.NUM_COLORS * img.width;
    color_indices.forEach(function(i) {
        if ((i == 0) || (i == 1) || (i ==2)) {
            img.data[x + y + i] = luminosity;
        } else {
            console.log('error: set_pixel_color accessed color outside rgb');
        }
    });
}

CanvImg.strip_alpha_channel = function(img) {
    // sets an image's alpha channel to opaque
    for (var i = CanvImg.ALPHA; i < img.data.length; i += CanvImg.NUM_COLORS) {
        img.data[i] = CanvImg.OPAQUE;
    }
}

CanvImg.get_greyscale = function(img) {
    // return a grayscaled copy of img
    var img = CanvImg.copy_image(img),
        data = img.data,
        scaling = [0.299, 0.587, 0.114],
        greyscale,
        r, g, b;
    for (var i = 0; i < data.length; i += CanvImg.NUM_COLORS) {
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

})();
