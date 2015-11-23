/* hold onto canny-edge finding related variables and functions
 */

Canny = {};

(function() {
"use strict";

Canny.calculate_edge_magnitude(x_edge, y_edge) {
    if !(x_edge.length == y_edge.length) {
        console.log('uh oh. x_edge and y_edge are not same size for mag');
    }
    var magnitude = new Array(x_edge.length),
        length = x_edge.length,
        i, x, y,
        mag_squared;
    for (i = 0; i < length; i++) {
        x = x_edge[i];
        y = y_edge[i];
        mag_squared = Math.pow(x, 2) + Math.pow(y, 2);
        magnitude[i] = Math.sqrt(mag_squared);
    }
    return magnitude;
}


})();
