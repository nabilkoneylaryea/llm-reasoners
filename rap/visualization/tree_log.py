from typing import Sequence, Union

from rap.algorithm import MCTSNode, MCTSResult
from rap.visualization.tree_snapshot import NodeId, EdgeId, TreeSnapshot, NodeData, EdgeData


class TreeLog:
    def __init__(self, tree_snapshots: Sequence[TreeSnapshot]) -> None:
        self._tree_snapshots = tree_snapshots

    def __getitem__(self, item):
        return self._tree_snapshots[item]

    def __iter__(self):
        return iter(self._tree_snapshots)

    def __len__(self):
        return len(self._tree_snapshots)

    @classmethod
    def from_mcts_results(cls, mcts_results: MCTSResult) -> 'TreeLog':

        def get_reward(n: MCTSNode) -> Union[dict, None]:
            if hasattr(n, "reward_details"):
                return n.reward_details
            return n.fast_reward_details if hasattr(n, "fast_reward_details") else None

        def node_data_factory(n: MCTSNode) -> NodeData:
            return NodeData({"state": n.state.blocks_state if n.state else None})

        def edge_data_factory(n: MCTSNode) -> EdgeData:
            return EdgeData({"Q": n.Q, **get_reward(n)})

        snapshots = []

        def all_nodes(node: MCTSNode):
            node_id = NodeId(node.id)

            nodes[node_id] = TreeSnapshot.Node(node_id, node_data_factory(node))
            if node.children is None:
                return
            for child in node.children:
                edge_id = EdgeId(len(edges))
                edges.append(TreeSnapshot.Edge(edge_id, node.id, child.id, edge_data_factory(child)))
                all_nodes(child)

        for step in range(len(mcts_results.tree_state_after_each_iter)):
            edges = []
            nodes = {}

            root = mcts_results.tree_state_after_each_iter[step]
            all_nodes(root)
            tree = TreeSnapshot(list(nodes.values()), edges)

            # select edges with highest Q value
            for node in tree.nodes.values():
                if node.selected_edge is None and tree.children(node.id):
                    node.selected_edge = max(
                        tree.out_edges(node.id),
                        key=lambda edge: edge.data.get("Q", -float("inf"))
                    ).id

            snapshots.append(tree)

        return cls(snapshots)
