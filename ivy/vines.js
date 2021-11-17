/*
  @licstart  The following is the entire license notice for the
  JavaScript code in this page.

  Copyright (C) 2021 G. Giamarchi

  The JavaScript code in this page is free software: you can
  redistribute it and/or modify it under the terms of the GNU
  General Public License (GNU GPL) as published by the Free Software
  Foundation, either version 3 of the License, or (at your option)
  any later version.  The code is distributed WITHOUT ANY WARRANTY;
  without even the implied warranty of MERCHANTABILITY or FITNESS
  FOR A PARTICULAR PURPOSE.  See the GNU GPL for more details.

  As additional permission under GNU GPL version 3 section 7, you
  may distribute non-source (e.g., minimized or compacted) forms of
  that code without the copy of the GNU GPL normally required by
  section 4, provided you include this license notice and a URL
  through which recipients can access the Corresponding Source.

  @licend  The above is the entire license notice
  for the JavaScript code in this page.
*/

const canvas = document.getElementById("canvasvines");
const ctx = canvas.getContext("2d");
const framerate = 44;

// ctx.shadowBlur = 50;
// ctx.shadowColor = "black";

ctx.globalAlpha = 0.8;

// This arrays holds a list of drawing orders that need to be
// executed.  This allows to store the recursive calls, but also
// execute them when we want.
var drawfuncs = [];

function getMousePos(canvas, evt) {
    var rect = canvas.getBoundingClientRect();
    return {
	x: evt.clientX - rect.left,
	y: evt.clientY - rect.top
    };
}

function randomFloat(l,h) {
    return Math.random() * (h - l) + l;
}

function randomInt(l,h) {
    return Math.floor(Math.random() * (h - l) + l);
}

function clear() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    clearDrawFuncs();
    noise.seed(Math.random());
}

function resizeCanvas() {
    /* Make canvas full screen */
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    clear();
}

function vec(x, y) {
    return {x : x, y : y};
}

/* Polar */
function vecp(n, angle) {
    return vec(n * Math.cos(angle), n * Math.sin(angle));
}

function scale(v, l) {
    return {x : v.x * l, y : v.y * l};
}

function norm(v) {
    return Math.sqrt(v.x ** 2 + v.y ** 2);
}

/* Limit vector norm */
function limit(v, n) {
    vn = norm(v);
    if(vn < n) {
	return;
    }
    v.x *= (n/vn);
    v.y *= (n/vn);
}

/* Returns perlin noise in [0,1] */
function perlin2d(x, y){
    return (noise.perlin2(x,y)+1) * 0.5;
}

function drawnoise() {
    var image = ctx.createImageData(canvas.width, canvas.height);
    var data = image.data;
    for (var x = 0; x < canvas.width; x++) {
	for (var y = 0; y < canvas.height; y++) {
	    var value = perlin2d(x/100, y/100) * 256;
	    var cell = (x + y * canvas.width) * 4;
	    data[cell] = data[cell + 1] = data[cell + 2] = value;
	    data[cell] += Math.max(0, (25 - value) * 8);
	    data[cell + 3] = 255; // alpha.
	}
    }
    ctx.putImageData(image, 0, 0);
}

/*
  Leaf central axis:

  h   0......c...m...........(vx,vy)

  c -> Intersection of central axis and line between two
  outermost leaf vertices (convex spikes).

  m -> Intersection of central axis and line between two
  inner leaf vertices (concave)

  h -> Same as ^, with intersection of leftmost (outer) points.

*/
function leaf(x, y, v, w, col, alpha) {
    /* Update x,y to have an imaginary stem */
    x += randomFloat(0.4,0.6) * v.x;
    y += randomFloat(0.4,0.6) * v.y;

    /* randomize control vectors somewhat */
    v.x += randomInt(-2,2);
    v.y += randomInt(-2,2);
    w.x += randomInt(-2,2);
    w.y += randomInt(-2,2);
    v = scale(v, randomFloat(1,1.3));
    w = scale(w, randomFloat(1,1.3));

    /* generate central axix intersection pts */
    let cx = x + v.x * 0.3
    let cy = y + v.y * 0.3
    let mx = cx + 0.1 * v.x
    let my = cy + 0.1 * v.y
    let hx = x - 0.3 * v.x
    let hy = y - 0.3 * v.y
    let r = 0.4;

    /* main leaf */
    ctx.strokeStyle = `rgba(0,0,0,${alpha})`;
    ctx.fillStyle = `rgba(${col.r},${col.g},${col.b},${alpha})`;

    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(hx - w.x/2, hy - w.y/2, cx - w.x, cy - w.y);
    ctx.lineTo(mx - r * w.x, my - r * w.y);
    ctx.lineTo(x + v.x, y + v.y);
    ctx.lineTo(mx + r * w.x, my + r * w.y);
    ctx.lineTo(cx + w.x, cy + w.y);
    ctx.quadraticCurveTo(hx + w.x/2, hy + w.y/2, x, y);  /* manually close */
    ctx.fill();
    ctx.stroke();

    /* leaf lines */
    ctx.lineCap = "round";
    ctx.strokeStyle = "white";

    ctx.beginPath()
    ctx.moveTo(x, y);
    ctx.lineTo(cx - w.x, cy - w.y);
    ctx.moveTo(x, y);
    ctx.lineTo(x + v.x, y + v.y);
    ctx.moveTo(x, y);
    ctx.lineTo(cx + w.x, cy + w.y);
    ctx.stroke();
}

/*
  function testLeaf(x, y) {
  let v = vecp(17, 0);
  let w = vecp(13, Math.PI/2);
  leaf(x,y,v,w);
  v = vecp(80, 0 + 1 );
  w = vecp(60, Math.PI/2 + 1);
  leaf(x + 100,y + 100,v,w);
  }
  testLeaf(500, 500); */

function openLeaf(x,y,w1,w2,col,alpha) {
    /* low alpha, because leaves will get overlayed
       high in first frames, to see animation start. */
    var l1 = () => {
	leaf(x, y, scale(w1, 0.4), scale(w2, 0.2), col, alpha*0.8);
	drawfuncs.push(l2);
    }
    var l2 = () => {
	leaf(x, y, scale(w1, 0.5), scale(w2, 0.3), col, alpha*0.7);
	drawfuncs.push(l3);
    }
    var l3 = () => {
	leaf(x, y, scale(w1, 0.7), scale(w2, 0.5), col, alpha*0.4);
	drawfuncs.push(l4);
    }
    var l4 = () => {
	leaf(x, y, scale(w1, 0.8), scale(w2, 0.6), col, alpha*0.5);
	drawfuncs.push(l5);
    }
    var l5 = () => {
	leaf(x, y, scale(w1, 0.9), scale(w2, 0.9), col, alpha*0.5);
	drawfuncs.push(l6);
    }
    var l6 = () => {
	leaf(x, y, w1, w2, col, alpha*0.5);
    }
    return l1;
}

function makeVinetip(x, y, rsize, age, maxage, col) {

    /* Velocity */
    var vdecay = randomFloat(0.75, 0.90);
    var va = Math.random()*2*Math.PI; /* vel. angle */
    var vn = randomFloat(0,5)         /* vel. norm  */
    var v = vecp(vn, va);

    function tip() {
	age += 1;

	var u = (maxage - age) / maxage;
	var alpha = 1;
	var size = u * rsize;

	/* stop this vine's growth by age or if too small */
	if(age > maxage || size < 1){
	    return;
	}

	ctx.fillStyle = `rgba(${col.r},${col.g},${col.b},${u})`;
	ctx.strokeStyle = `rgba(0,0,0,${u*0.8})`;
	ctx.lineWidth = 1;

	ctx.beginPath();
	ctx.arc(x, y, size, 0, 2 * Math.PI);
	ctx.fill();
	ctx.stroke();

	/* recurse */
	drawfuncs.push(tip)
	/*
	  if(age == Math.floor(maxage/4)){
	  drawfuncs.push(makeVinetip(x,y,size,age,maxage,col));
	  } */

	/* spawning leaves */
	if(Math.random() > 0.9){
	    let angle = Math.atan2(v.y,v.x);
	    angle += (Math.PI / 2) *
		(Math.random() > 0.5 ? randomFloat(0.8,0.8): - randomFloat(0.8,0.8))
	    let w1 = vecp(17*0.8, angle);
	    let w2 = vecp(13*0.8, angle + Math.PI/2);
	    // let col = {r: randomInt(30,130), g: randomInt(80,200), b: randomInt(0,80)};
	    let col = {r: randomInt(30,255), g: randomInt(200,255), b: randomInt(0,80)};
	    drawfuncs.push(openLeaf(x,y,w1,w2,col,alpha));
	}

	/* Update */

	/* Acceleration */
	//console.log(noise.perlin2(x*100, y*100));
	let aa = perlin2d(x/100,y/100) * 4 * Math.PI;
	let an = perlin2d(x/100,y/100 - 0.3);
	let a = vecp(an, aa);
	//console.log(a);

	v.x += a.x;
	v.y += a.y;

	let randv = vecp(0.8, randomFloat(0,2*Math.PI));
	v.x += randv.x;
	v.y += randv.y;

	v.x *= vdecay;
	v.y *= vdecay;
	limit(v, 3);

	x += v.x;
	y += v.y;
    }

    return tip;
}

function spawnvine(evt) {
    //console.log("spawning");
    let mpos =	getMousePos(canvas, evt);
    let rsize = randomInt(2,4);                   /* root size */
    let age = 0;
    let maxage = randomInt(250,500);
    //let col = {r: randomInt(0,200), g: randomInt(200,255), b: randomInt(0,200)};
    let col = {r: 130 + randomInt(-50,50), g: 100 + randomInt(-40,40), b: 60 + randomInt(-20,20)};
    drawfuncs.push(makeVinetip(mpos.x, mpos.y, rsize, age, maxage, col))
}

function clearDrawFuncs() {
    drawfuncs = Array();
}

/* Executes all functions in the drawfunc stack, and empty the stack */
function execDrawFuncs() {
    if(drawfuncs.length == 0) {
	console.log("Nothing to do");
    }
    var funcs = drawfuncs.slice();
    clearDrawFuncs();
    funcs.forEach(function(df){df.call()});
}

//The following two functions are taken from the javascript underscore
//library: http://underscorejs.org/
unow = Date.now || function() {
    return new Date().getTime();
};

uthrottle = function(func, wait, options) {
    var timeout, context, args, result;
    var previous = 0;
    if (!options) options = {};

    var later = function() {
	previous = options.leading === false ? 0 : unow();
	timeout = null;
	result = func.apply(context, args);
	if (!timeout) context = args = null;
    };

    var throttled = function() {
	var now = unow();
	if (!previous && options.leading === false) previous = now;
	var remaining = wait - (now - previous);
	context = this;
	args = arguments;
	if (remaining <= 0 || remaining > wait) {
	    if (timeout) {
		clearTimeout(timeout);
		timeout = null;
	    }
	    previous = now;
	    result = func.apply(context, args);
	    if (!timeout) context = args = null;
	} else if (!timeout && options.trailing !== false) {
	    timeout = setTimeout(later, remaining);
	}
	return result;
    };

    throttled.cancel = function() {
	clearTimeout(timeout);
	previous = 0;
	timeout = context = args = null;
    };

    return throttled;
};

let planting = false;

document.addEventListener("mousedown", (e) => {planting = true; spawnvine(e)});
document.addEventListener("mouseup", (e) => {planting = false;});
/* stop planting if canvas is left */
document.addEventListener("mouseleave", (e) => {planting = false;});
document.addEventListener("mousemove", (e) => {
    if(planting){
	spawnvine(e);
    }
});
/* clear screen bound to 'c' */
document.addEventListener("keydown", (e) => {
    if (e.isComposing || e.keyCode == 229) {
	return;
    }
    if (e.keyCode == 67) {    /* == 'c' */
	clear();
    }
});

/* Sets canvas to full screen, and hook on resize. */
resizeCanvas();
window.addEventListener("resize", (e) => {console.log("resized"); resizeCanvas()});

setInterval(execDrawFuncs, 1000 / framerate);
