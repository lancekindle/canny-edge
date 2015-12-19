
PageHelper = {};

(function() {
"use strict";

// =================== Moving edge-highlighted split images ==================
PageHelper.move_canvas_once = function(event, ymove, xmove) {
    var element = event.target;
    element.onclick="return true;"; // prevent more clicks from happening on this element
    //move element down (z-index) if it is separating from group
    //if image is heading back into the group, set z-index to global ++ZINDEX
    var eparent = element.parentElement;
    var firstchild = eparent.children[0];
    if (element["z-index"] == 0) {
        element["z-index"] = ++PageHelper.ZINDEX;
        // re-order elements so that this one is last (highest)
        eparent.appendChild(element);
    } else {
        element["z-index"] = 0;
        // re-order elements so that this one is first (lowest)
        eparent.insertBefore(element, firstchild);
    }
    //ymove and xmove are %s to move
    var t = 600, //300 millisecond transition time
        x = xmove / t,
        y = ymove / t,
        original_left = parseInt(element.style.left),  // "50%" => 50
        original_top = parseInt(element.style.top),
        left = original_left,
        top = original_top;
    var increment_element_position = function() {
        left += x;
        top += y;
        t -= 1;
        element.style.top = top + "%";
        element.style.left = left + "%";
        if (t != 0) {
            setTimeout(function() { increment_element_position(); }, 3);
        } else { // runs right before fxn ends
            //precisely align image
            element.style.top = (original_top + ymove) + "%";
            element.style.left = (original_left + xmove) + "%";
            //set fxn to move image back to original position
            element.onclick = function(event) { PageHelper.move_canvas_once(event, -ymove, -xmove); };
        }
    }
    setTimeout(function() { increment_element_position(); }, 3);
    return true; // return false to prevent event from reaching other layers
}

// ============================ Thresholding Image ================================
PageHelper.get_strong_weak_input = function() {
    var strong = parseInt(strong_threshold_input.value);
    var weak = parseInt(weak_threshold_input.value);
    return [strong, weak];
}

PageHelper.set_strong_weak_values = function(strong, weak) {
    // if only one value is defined, check that the other is in bounds and
    // correct value if necessary
    var sw;
    if (weak === undefined) {
        sw = PageHelper.get_strong_weak_input();
        weak = sw[1];
        if (strong <= weak)
            weak = strong - 1;
    }
    if (strong === undefined) {
        sw = PageHelper.get_strong_weak_input();
        strong = sw[0];
        if (strong <= weak)
            strong = weak + 1;
    }
    // now set strong and weak values
    strong_threshold_slider.value = strong;
    strong_threshold_input.value = strong;
    weak_threshold_slider.value = weak;
    weak_threshold_input.value = weak;
}

PageHelper.apply_threshold_changes = function(event) {
    var sw = PageHelper.get_strong_weak_input();
    var strong = sw[0];
    var weak = sw[1];
    //call function defined in script ImgProcess.js
    step8_threshold_thin_image(window.steps, strong, weak);
}

PageHelper.update_weak_threshold = function(event) {
    var e = event.target;
    var weak = parseInt(e.value);
    PageHelper.set_strong_weak_values(undefined, weak);
    PageHelper.apply_threshold_changes(event);
}

PageHelper.update_strong_threshold = function(event) {
    var e = event.target;
    var strong = parseInt(e.value);
    PageHelper.set_strong_weak_values(strong, undefined);
    PageHelper.apply_threshold_changes(event);
}

}())
