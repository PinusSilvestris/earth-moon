import streamlit as st
import json
import base64

st.set_page_config(page_title="Sun-Earth-Moon System", layout="wide")

st.title("Sun-Earth-Moon Orbital Visualization")
st.markdown("""
**Key insight:** At real orbital speeds, the Moon never makes loops from the Sun's perspective.
Increase the Moon's speed to 30x+ to see loops appear!
""")

# Sidebar controls
st.sidebar.header("Orbital Speed Controls")

earth_speed = st.sidebar.slider(
    "Earth orbital speed multiplier",
    min_value=0.1,
    max_value=5.0,
    value=1.0,
    step=0.1,
)

moon_speed = st.sidebar.slider(
    "Moon orbital speed multiplier",
    min_value=0.1,
    max_value=50.0,
    value=1.0,
    step=0.5,
)

st.sidebar.header("Animation Controls")

seconds_per_day = st.sidebar.slider(
    "Seconds per day",
    min_value=0.1,
    max_value=60.0,
    value=48.0,
    step=0.1,
)

st.sidebar.header("Camera")
follow_earth = st.sidebar.checkbox("Follow Earth", value=False)
zoom_level = st.sidebar.slider(
    "Zoom level",
    min_value=0.1,
    max_value=10.0,
    value=1.0,
    step=0.1,
    help="Higher = more zoomed in"
)

st.sidebar.header("Trace Visibility")
show_earth_trace = st.sidebar.checkbox("Show Earth trace", value=True)
show_moon_trace = st.sidebar.checkbox("Show Moon trace", value=True)
trail_days = st.sidebar.slider("Trail length (days)", 10, 400, 100, 10)

st.sidebar.header("Vector Visualization")
show_sun_earth = st.sidebar.checkbox("Sun → Earth", value=False)
show_sun_moon = st.sidebar.checkbox("Sun → Moon", value=False)
show_earth_moon = st.sidebar.checkbox("Earth → Moon", value=True)

# Pass config to JavaScript
config = {
    "earthSpeed": earth_speed,
    "moonSpeed": moon_speed,
    "secondsPerDay": seconds_per_day,
    "followEarth": follow_earth,
    "zoomLevel": zoom_level,
    "showEarthTrace": show_earth_trace,
    "showMoonTrace": show_moon_trace,
    "trailDays": trail_days,
    "showSunEarth": show_sun_earth,
    "showSunMoon": show_sun_moon,
    "showEarthMoon": show_earth_moon,
}

html_code = f"""
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ margin: 0; overflow: hidden; background: #0a0a1a; }}
    canvas {{ display: block; }}
    #controls {{
        position: absolute;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        display: flex;
        gap: 10px;
        z-index: 100;
    }}
    button {{
        padding: 8px 20px;
        font-size: 14px;
        cursor: pointer;
        background: #333;
        color: white;
        border: 1px solid #555;
        border-radius: 4px;
    }}
    button:hover {{ background: #444; }}
    #info {{
        position: absolute;
        top: 10px;
        left: 10px;
        color: #aaa;
        font-family: monospace;
        font-size: 12px;
    }}
    #status {{
        position: absolute;
        top: 10px;
        right: 10px;
        color: #aaa;
        font-family: monospace;
        font-size: 14px;
        padding: 5px 10px;
        background: rgba(0,0,0,0.5);
        border-radius: 4px;
    }}
</style>
</head>
<body>
<canvas id="canvas"></canvas>
<div id="controls">
    <button id="zoomIn">Zoom +</button>
    <button id="zoomOut">Zoom -</button>
    <button id="playPause">Pause</button>
    <button id="reset">Reset</button>
</div>
<div id="info">Drag to pan | Double-click to reset view</div>
<div id="status"></div>

<script>
const config = {json.dumps(config)};

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

// Constants (real scale)
const EARTH_PERIOD = 365.25;  // days
const MOON_PERIOD = 27.3;     // days
const EARTH_RADIUS = 1.0;     // AU
const MOON_RADIUS = 0.00257;  // AU (real scale)

// State
let currentDay = 0;
let playing = true;
let lastTime = performance.now();

// View state
let viewX = 0;
let viewY = 0;
let userZoom = 1;  // User-controlled zoom multiplier
const baseScale = 300;  // pixels per AU
let viewScale = baseScale;  // Current view scale (updated in draw)

// Trails
let earthTrail = [];
let moonTrail = [];
const maxTrailPoints = 5000;

// Resize canvas
function resize() {{
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}}
window.addEventListener('resize', resize);
resize();

// Calculate positions
function getPositions(day) {{
    const earthOmega = (2 * Math.PI / EARTH_PERIOD) * config.earthSpeed;
    const moonOmega = (2 * Math.PI / MOON_PERIOD) * config.moonSpeed;

    const earthX = EARTH_RADIUS * Math.cos(earthOmega * day);
    const earthY = EARTH_RADIUS * Math.sin(earthOmega * day);

    const moonRelX = MOON_RADIUS * Math.cos(moonOmega * day);
    const moonRelY = MOON_RADIUS * Math.sin(moonOmega * day);

    return {{
        earth: {{ x: earthX, y: earthY }},
        moon: {{ x: earthX + moonRelX, y: earthY + moonRelY }}
    }};
}}

// World to screen coordinates
function toScreen(x, y) {{
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    return {{
        x: cx + (x - viewX) * viewScale,
        y: cy - (y - viewY) * viewScale  // flip Y
    }};
}}

// Draw arrow
function drawArrow(fromX, fromY, toX, toY, color) {{
    const from = toScreen(fromX, fromY);
    const to = toScreen(toX, toY);

    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Arrowhead
    const angle = Math.atan2(to.y - from.y, to.x - from.x);
    const headLen = 10;
    ctx.beginPath();
    ctx.moveTo(to.x, to.y);
    ctx.lineTo(to.x - headLen * Math.cos(angle - 0.3), to.y - headLen * Math.sin(angle - 0.3));
    ctx.lineTo(to.x - headLen * Math.cos(angle + 0.3), to.y - headLen * Math.sin(angle + 0.3));
    ctx.closePath();
    ctx.fillStyle = color;
    ctx.fill();
}}

// Draw trail
function drawTrail(trail, color) {{
    if (trail.length < 2) return;

    ctx.beginPath();
    const start = toScreen(trail[0].x, trail[0].y);
    ctx.moveTo(start.x, start.y);

    for (let i = 1; i < trail.length; i++) {{
        const p = toScreen(trail[i].x, trail[i].y);
        ctx.lineTo(p.x, p.y);
    }}

    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.stroke();
}}

// Main draw function
function draw() {{
    // Clear
    ctx.fillStyle = '#0a0a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const pos = getPositions(currentDay);

    // Follow Earth
    if (config.followEarth) {{
        viewX = pos.earth.x;
        viewY = pos.earth.y;
    }}

    // Calculate view scale from config and user zoom
    viewScale = baseScale * config.zoomLevel * userZoom;

    // Draw Earth orbit (reference)
    ctx.beginPath();
    const orbitCenter = toScreen(0, 0);
    ctx.arc(orbitCenter.x, orbitCenter.y, EARTH_RADIUS * viewScale, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(100, 100, 255, 0.2)';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Draw trails
    if (config.showEarthTrace) {{
        drawTrail(earthTrail, 'rgba(100, 150, 255, 0.6)');
    }}
    if (config.showMoonTrace) {{
        drawTrail(moonTrail, 'rgba(200, 200, 200, 0.6)');
    }}

    // Draw vectors
    if (config.showSunEarth) {{
        drawArrow(0, 0, pos.earth.x, pos.earth.y, '#ffa500');
    }}
    if (config.showSunMoon) {{
        drawArrow(0, 0, pos.moon.x, pos.moon.y, '#ff4444');
    }}
    if (config.showEarthMoon) {{
        drawArrow(pos.earth.x, pos.earth.y, pos.moon.x, pos.moon.y, '#44ff44');
    }}

    // Draw Sun
    const sunPos = toScreen(0, 0);
    ctx.beginPath();
    ctx.arc(sunPos.x, sunPos.y, 15, 0, Math.PI * 2);
    ctx.fillStyle = '#ffdd00';
    ctx.fill();
    ctx.strokeStyle = '#ffaa00';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Draw Earth
    const earthPos = toScreen(pos.earth.x, pos.earth.y);
    ctx.beginPath();
    ctx.arc(earthPos.x, earthPos.y, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#4488ff';
    ctx.fill();

    // Draw Moon
    const moonPos = toScreen(pos.moon.x, pos.moon.y);
    ctx.beginPath();
    ctx.arc(moonPos.x, moonPos.y, 4, 0, Math.PI * 2);
    ctx.fillStyle = '#cccccc';
    ctx.fill();

    // Status
    const earthPeriod = (EARTH_PERIOD / config.earthSpeed).toFixed(1);
    const moonPeriod = (MOON_PERIOD / config.moonSpeed).toFixed(1);

    // Check for loops
    const earthV = EARTH_RADIUS * (2 * Math.PI / EARTH_PERIOD) * config.earthSpeed;
    const moonV = MOON_RADIUS * (2 * Math.PI / MOON_PERIOD) * config.moonSpeed;
    const loopStatus = moonV > earthV ? "LOOPS!" : "Smooth wave";

    document.getElementById('status').innerHTML =
        `Day: ${{currentDay.toFixed(1)}} | Earth: ${{earthPeriod}}d | Moon: ${{moonPeriod}}d | Path: ${{loopStatus}}`;
}}

// Animation loop
function animate(time) {{
    if (playing) {{
        const dt = (time - lastTime) / 1000;  // seconds
        const dayStep = dt / config.secondsPerDay;  // days per frame
        currentDay += dayStep;

        // Update trails
        const pos = getPositions(currentDay);
        earthTrail.push({{ x: pos.earth.x, y: pos.earth.y }});
        moonTrail.push({{ x: pos.moon.x, y: pos.moon.y }});

        // Trim trails based on trail length setting
        const framesPerDay = 60 * config.secondsPerDay;  // approximate
        const maxPoints = Math.min(config.trailDays * framesPerDay, maxTrailPoints);
        while (earthTrail.length > maxPoints) earthTrail.shift();
        while (moonTrail.length > maxPoints) moonTrail.shift();
    }}

    lastTime = time;
    draw();
    requestAnimationFrame(animate);
}}

// Controls
document.getElementById('playPause').addEventListener('click', () => {{
    playing = !playing;
    document.getElementById('playPause').textContent = playing ? 'Pause' : 'Play';
}});

document.getElementById('reset').addEventListener('click', () => {{
    currentDay = 0;
    earthTrail = [];
    moonTrail = [];
    viewX = 0;
    viewY = 0;
}});

// Mouse controls
let isDragging = false;
let dragStartX, dragStartY;
let dragStartViewX, dragStartViewY;

canvas.addEventListener('mousedown', (e) => {{
    isDragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    dragStartViewX = viewX;
    dragStartViewY = viewY;
}});

canvas.addEventListener('mousemove', (e) => {{
    if (isDragging && !config.followEarth) {{
        const currentScale = baseScale * config.zoomLevel * userZoom;
        const dx = (e.clientX - dragStartX) / currentScale;
        const dy = (e.clientY - dragStartY) / currentScale;
        viewX = dragStartViewX - dx;
        viewY = dragStartViewY + dy;  // flip Y
    }}
}});

canvas.addEventListener('mouseup', () => {{ isDragging = false; }});
canvas.addEventListener('mouseleave', () => {{ isDragging = false; }});

canvas.addEventListener('dblclick', () => {{
    viewX = 0;
    viewY = 0;
    userZoom = 1;
}});

// Zoom buttons
document.getElementById('zoomIn').addEventListener('click', () => {{
    userZoom *= 1.5;
    userZoom = Math.min(1000, userZoom);
}});

document.getElementById('zoomOut').addEventListener('click', () => {{
    userZoom /= 1.5;
    userZoom = Math.max(0.1, userZoom);
}});

// Start
requestAnimationFrame(animate);
</script>
</body>
</html>
"""

html_bytes = html_code.encode('utf-8')
data_uri = f"data:text/html;base64,{base64.b64encode(html_bytes).decode()}"
st.iframe(data_uri, height=650)

# Info panel
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    ### Controls:
    - **Zoom +/-** buttons to zoom
    - **Drag** - Pan view (disabled in Follow mode)
    - **Double-click** - Reset view
    """)
with col2:
    st.markdown("""
    ### Physics:
    - Moon orbit: 384,400 km (0.26% of Earth's orbit)
    - At real speeds, Moon never loops
    - Loops appear at ~29x moon speed
    """)
