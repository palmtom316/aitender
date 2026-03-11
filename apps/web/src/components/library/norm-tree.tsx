"use client";

import React from "react";

import type { NormTreeNode } from "../../lib/api/norms";

type NormTreeProps = {
  nodes: NormTreeNode[];
  selectedLabel: string | null;
};

export function NormTree({ nodes, selectedLabel }: NormTreeProps) {
  return (
    <section aria-label="Norm tree">
      <h2>Structure</h2>
      <ul role="tree">
        {nodes.map((node) => (
          <TreeNodeItem key={node.label} node={node} selectedLabel={selectedLabel} />
        ))}
      </ul>
    </section>
  );
}

type TreeNodeItemProps = {
  node: NormTreeNode;
  selectedLabel: string | null;
};

function TreeNodeItem({ node, selectedLabel }: TreeNodeItemProps) {
  return (
    <li
      aria-current={selectedLabel === node.label ? "true" : undefined}
      role="treeitem"
    >
      <span data-testid={selectedLabel === node.label ? "active-tree-node" : undefined}>
        {node.label}
      </span>
      {node.children && node.children.length > 0 ? (
        <ul role="group">
          {node.children.map((child) => (
            <TreeNodeItem key={child.label} node={child} selectedLabel={selectedLabel} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}
