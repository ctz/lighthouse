var cfgGraphWidth = 100;
var cfgBasicBlockMargin = 5;
var quad = true;
var inArrows = {};
var outArrows = {};
var edgeOpacity = '0.1';
var edgeColour = 'black';

function cfgArrow(r, fn, rank, start, end, offset)
{
  var start_e = document.getElementById('block_' + fn + '_' + start);
  var end_e = document.getElementById('block_' + fn + '_' + end);
  var container = document.getElementById('blocks_' + fn);
  var container_xy = container.getPosition();
    
  var start_xy = start_e.getPosition();
  start_xy.x = 1;
  start_xy.y -= container_xy.y;
  var end_xy = end_e.getPosition();
  end_xy.x = 1;
  end_xy.y -= container_xy.y;
  
  var start_wh = start_e.getSize();
  var end_wh = end_e.getSize();
  
  offset = offset * 12; // * fontsize
  depth = 5;
  arrow = 3;
  offs_x = (3 + rank) * depth;
  v = {
    "stroke": edgeColour,
    "stroke-width": 2,
    "stroke-linejoin": "round",
    "opacity": edgeOpacity,
  }
  
  var p = r.path(v).absolutely();
  midpoint = start_xy.y + start_wh.y;
  diff = end_xy.y - midpoint;
  midpoint += diff / 2;
  
  p.moveTo(start_xy.x, start_xy.y + start_wh.y + offset);
  
  if (quad)
  {
    p.qcurveTo(start_xy.x + offs_x, midpoint,
               end_xy.x, end_xy.y);
  } else {
    p.lineTo(start_xy.x + offs_x, start_xy.y + start_wh.y + offset);
    p.lineTo(end_xy.x + offs_x, end_xy.y);
    p.lineTo(end_xy.x, end_xy.y);
  }
   
  p.lineTo(end_xy.x + arrow, end_xy.y - arrow);
  p.moveTo(end_xy.x, end_xy.y);
  p.lineTo(end_xy.x + arrow, end_xy.y + arrow);
  
  key = fn + '_' + end;
  if (inArrows[key] == undefined)
    inArrows[key] = [];
  inArrows[key].push(p);
  
  key = fn + '_' + start;
  if (outArrows[key] == undefined)
    outArrows[key] = [];
  outArrows[key].push(p);
}

function setArrows(fn, bb, op, in_, out)
{
  key = fn + '_' + bb;
  
  if (0)
  {
  for (var p in inArrows[key])
  {
    if (inArrows[key][p].attr != undefined)
    {
      inArrows[key][p].attr('opacity', op);
      inArrows[key][p].attr('stroke', in_);
    }
  }
  }
  
  for (var p in outArrows[key])
  {
    if (outArrows[key][p].attr != undefined)
    {
      outArrows[key][p].attr('opacity', op); 
      outArrows[key][p].attr('stroke', out);
    }
  }
}

function highlightArrows(fn, bb)
{
  setArrows(fn, bb, '1.0', 'green', 'blue');
}

function unhighlightArrows(fn, bb)
{
  setArrows(fn, bb, edgeOpacity, edgeColour, edgeColour);
}
