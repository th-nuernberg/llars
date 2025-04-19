<template>
  <svg ref="svg" class="svg-content"></svg>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import * as d3 from 'd3';

const props = defineProps({
  data: { type: Object, required: true }
});

const svg = ref(null);

function drawGraph() {
  const graph = props.data;
  if (!graph || !graph.Akteure || !graph.Beziehungen) return;
  const nodes = graph.Akteure;
  const links = graph.Beziehungen.map(l => ({ source: l.source, target: l.target }));
  const nodeById = Object.fromEntries(nodes.map(n => [n.ID, n]));
  links.forEach(l => {
    l.source = nodeById[l.source];
    l.target = nodeById[l.target];
  });
  const width = 400;
  const height = 300;
  const svgSel = d3.select(svg.value);
  svgSel.selectAll('*').remove();
  svgSel.attr('viewBox', `0 0 ${width} ${height}`);
  // draw vertical and horizontal divider lines at center
  const centerX = width / 2;
  const centerY = height / 2;
  svgSel.append('line')
    .attr('x1', centerX).attr('y1', 0)
    .attr('x2', centerX).attr('y2', height)
    .attr('stroke', '#bbb')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '4 2');
  svgSel.append('line')
    .attr('x1', 0).attr('y1', centerY)
    .attr('x2', width).attr('y2', centerY)
    .attr('stroke', '#bbb')
    .attr('stroke-width', 1)
    .attr('stroke-dasharray', '4 2');
  // Place nodes within their quadrant, offset from axes
  const radius = Math.min(width, height) * 0.4;
  const deg = Math.PI / 180;
  const sectorAngleRanges = {
    'Freunde/Bekannte': [ -Math.PI/2 + 10*deg, -10*deg ],   // top right: -80° to -10°
    'Schule/Beruf':     [  10*deg,          Math.PI/2 - 10*deg ], // bottom right: 10° to 80°
    'Professionelle':   [  Math.PI/2 + 10*deg, Math.PI - 10*deg ],  // bottom left: 100° to 170°
    'Familie':          [ -Math.PI + 10*deg, -Math.PI/2 - 10*deg ]  // top left: -170° to -100°
  };
  nodes.forEach(n => {
    if (n.Sektor === 'Ratsuchend') {
      n.x = centerX;
      n.y = centerY;
    } else if (sectorAngleRanges[n.Sektor]) {
      const [minA, maxA] = sectorAngleRanges[n.Sektor];
      const angle = minA + Math.random() * (maxA - minA);
      n.x = centerX + Math.cos(angle) * radius;
      n.y = centerY + Math.sin(angle) * radius;
    } else {
      n.x = centerX;
      n.y = centerY;
    }
  });
  // Run a short force simulation for collision detection (avoid overlaps)
  const simulation = d3.forceSimulation(nodes)
    .force('x', d3.forceX(d => d.x).strength(1))
    .force('y', d3.forceY(d => d.y).strength(1))
    .force('collide', d3.forceCollide().radius(d => ((d.Sektor === 'Ratsuchend' ? 10 : 8) + 5)))
    .stop();
  for (let i = 0; i < 200; ++i) simulation.tick();
  const linkSel = svgSel.append('g')
    .attr('stroke', '#999')
    .attr('stroke-opacity', 0.6)
    .selectAll('line')
    .data(links)
    .enter().append('line')
    .attr('stroke-width', 1.5);

  // Create node groups with circle and label
  const nodeGroup = svgSel.append('g')
    .selectAll('g')
    .data(nodes)
    .enter().append('g')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      })
    );
  // Append circles (help-seeking person in red at center)
  nodeGroup.append('circle')
    .attr('r', d => d.Sektor === 'Ratsuchend' ? 10 : 8)
    .attr('fill', d => d.Sektor === 'Ratsuchend' ? 'red' : 'steelblue')
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5);
  // Append labels
  nodeGroup.append('text')
    .text(d => d.Name || d.ID)
    .attr('text-anchor', 'middle')
    .attr('dy', -12)
    .attr('fill', '#333')
    .style('font-size', '12px');

  // Draw links and nodes at computed positions
  linkSel
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y);
  nodeGroup.attr('transform', d => `translate(${d.x},${d.y})`);
}

onMounted(drawGraph);
watch(() => props.data, drawGraph);
</script>

<style scoped>
 .svg-content {
  width: 100%;
  height: 300px;
 }
</style>