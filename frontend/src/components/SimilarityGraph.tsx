import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { Cluster } from '../types';

interface SimilarityGraphProps {
  clusters: Cluster[];
}

interface GraphNode extends d3.SimulationNodeDatum {
  id: string;
  name: string;
  type: string;
  memberCount: number;
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  strength: number;
}

export function SimilarityGraph({ clusters }: SimilarityGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || clusters.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = 400;

    const nodes: GraphNode[] = clusters.map(c => ({
      id: c.id,
      name: c.name,
      type: c.cluster_type,
      memberCount: c.member_count,
    }));

    const links: GraphLink[] = [];
    // Create links between clusters of the same type
    for (let i = 0; i < clusters.length; i++) {
      for (let j = i + 1; j < clusters.length; j++) {
        if (clusters[i].cluster_type === clusters[j].cluster_type) {
          links.push({
            source: clusters[i].id,
            target: clusters[j].id,
            strength: 0.3,
          });
        }
      }
    }

    const colorMap: Record<string, string> = {
      exact_duplicate: '#ef4444',
      near_duplicate: '#f97316',
      family: '#3b82f6',
    };

    const simulation = d3
      .forceSimulation(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links).id(d => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    const g = svg.append('g');

    const link = g
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#e5e7eb')
      .attr('stroke-width', 1);

    const node = g
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => Math.max(8, Math.min(25, d.memberCount * 5)))
      .attr('fill', d => colorMap[d.type] || '#6b7280')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('cursor', 'pointer');

    const label = g
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text(d => d.name.length > 20 ? d.name.slice(0, 20) + '...' : d.name)
      .attr('font-size', '10px')
      .attr('fill', '#374151')
      .attr('text-anchor', 'middle')
      .attr('dy', d => Math.max(8, Math.min(25, d.memberCount * 5)) + 14);

    node.append('title').text(d => `${d.name}\nType: ${d.type}\nMembers: ${d.memberCount}`);

    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x!)
        .attr('y1', d => (d.source as GraphNode).y!)
        .attr('x2', d => (d.target as GraphNode).x!)
        .attr('y2', d => (d.target as GraphNode).y!);
      node.attr('cx', d => d.x!).attr('cy', d => d.y!);
      label.attr('x', d => d.x!).attr('y', d => d.y!);
    });

    // Zoom
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 3])
      .on('zoom', (event) => g.attr('transform', event.transform));
    svg.call(zoom);

    return () => { simulation.stop(); };
  }, [clusters]);

  if (clusters.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-500">No clusters to visualize. Run analysis first.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h3 className="font-semibold text-gray-800">Cluster Visualization</h3>
        <div className="flex gap-4 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-red-500" /> Exact Duplicates
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-orange-500" /> Near Duplicates
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-full bg-blue-500" /> Families
          </span>
        </div>
      </div>
      <svg ref={svgRef} width="100%" height={400} />
    </div>
  );
}
