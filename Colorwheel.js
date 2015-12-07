Colorwheel = {};

(function() {
"use strict";

Colorwheel.rgb_from_magnitude_and_angle = function(magnitude, angle) {
    /*create fully scaled (shaded) rgb arrays, where the rgb arrays have the
     * corresponding color ratios given the angle, and the corresponding
     * brightness given the magnitude.
     * Return 3 arrays: red, green, and blue.
     */
    var rgb = Colorwheel.rgb_from_angle(angle);
    Colorwheel.scale_rgb_with_intensity(rgb, magnitude);
    return rgb;
}

Colorwheel.scale_rgb_with_intensity = function(rgb, intensity_array) {
    /*given an array (0-255 values), scale a set of rgb arrays so that they
     * reflect the intensity_array in value. So if a intensity_array[i] = 0,
     * the rgb arrays @ index i will be 0. If intensity_array[i] = 127, then the
     * rgb values will be scaled appropriately. In this case, 127/255 ~ 1/2, so
     * the rgb values will be scaled to a half of their previous values
     * return new rgb object with 3 arrays: r, g, b
     */
    var r = rgb[0].slice(0),
        g = rgb[1].slice(0),
        b = rgb[2].slice(0),
        rgb = {
            0: r,
            1: g,
            2: b,
            red: r,
            green: g,
            blue: b
        };
    var len = intensity_array.length,
        scale,
        min = 0,
        max = 255,
        red = rgb[0],
        green = rgb[1],
        blue = rgb[2];
    for (var i = 0; i < len; i++) {
        scale = intensity_array[i] / 255;
        red[i] *= scale;
        green[i] *= scale;
        blue[i] *= scale;
    }
    return rgb
}

Colorwheel.rgb_from_angle = function(angle_array) {
    /* given an array representing angles, create 3 arrays representing red,
     * green, and blue in that order of the colorwheel values. Each value in
     * angle_array corresponds to a unique rgb value, and so each index of r,
     * g, and b will hold the corresponding unique value.
     * Return 3 arrays: red, green, and blue (in that order)
     */
    var len = angle_array.length,
        angle, color,
        r = new Array(len),
        g = new Array(len),
        b = new Array(len),
        cw = Colorwheel.get_colorwheel_array();
    for (var i = 0; i < len; i++) {
        angle = Math.floor(angle_array[i]);
        color = cw[angle];
        r[i] = color[0];
        g[i] = color[1];
        b[i] = color[2];
    }
    var rgb_array = {
        0: r,
        1: g,
        2: b,
        red: r,
        green: g,
        blue: b
    }
    return rgb_array;
}

Colorwheel.get_colorwheel_array = function() {
    /* Return an array representing a color wheel. The array contains 361
     * elements, each representing the rgb color at the corresponding angle, in
     * degrees. Each element is a 3-tuple, R, G, and B, whose values are 0-255.
     * the color wheel designed copies that from wikipedia, but rotated 30 deg:
     * https://en.wikipedia.org/wiki/Color_wheel#/media/File:RBG_color_wheel.svg
     * There are 361 elements instead of 360 because the first element is
     * duplicated as the last (extra) element, in case of index overrun.
     */
    var color_transition = function(colorwheel, start_angle, end_angle, color, change) {
        var angle_difference = end_angle - start_angle,
            red = color[0],
            green = color[1],
            blue = color[2],
            rc = change[0] / angle_difference,
            gc = change[1] / angle_difference,
            bc = change[2] / angle_difference;
        for (var i = start_angle; i < end_angle; i++) {
            red += rc;
            green += gc;
            blue += bc;
            colorwheel[i] = [red, green, blue];
        }
    }
    var colorwheel = new Array(360),
        color, change;
    //green to yellow (0, 255, 0) -> (255, 255, 0)
    color = [0, 255, 0];
    change = [255, 0, 0];
    color_transition(colorwheel, 0, 60, color, change);
    //yellow to red (255, 255, 0) - > (255, 0, 0)
    color = [255, 255, 0];
    change = [0, -255, 0];
    color_transition(colorwheel, 60, 120, color, change);
    //red to magenta (255, 0, 0) -> (255, 0, 255)
    color = [255, 0, 0];
    change = [0, 0, 255];
    color_transition(colorwheel, 120, 180, color, change);
    //magenta to blue (255, 0, 255) -> (0, 0, 255)
    color = [255, 0, 255];
    change = [-255, 0, 0];
    color_transition(colorwheel, 180, 240, color, change);
    //blue to aque (0, 0, 255) -> (0, 255, 255)
    color = [0, 0, 255];
    change = [0, 255, 0];
    color_transition(colorwheel, 240, 300, color, change);
    //aque to green (0, 255, 255) -> (0, 255, 0)
    color = [0, 255, 255];
    change = [0, 0, -255];
    color_transition(colorwheel, 300, 360, color, change);
    // and on the safe side, duplicate first element as extra last element
    colorwheel.push(colorwheel[0]);
    return colorwheel;
}

}())

