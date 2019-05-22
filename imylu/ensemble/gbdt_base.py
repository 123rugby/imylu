# -*- coding: utf-8 -*-
"""
@Author: tushushu
@Date: 2018-08-13 10:29:29
@Last Modified by:   tushushu
@Last Modified time: 2019-05-13 19:29:29
"""
from numpy import array
from numpy.random import choice
from typing import Dict, List
import numpy as np

from ..tree.regression_tree import RegressionTree, Node


class GradientBoostingBase:
    """GBDT base class.
    http://statweb.stanford.edu/~jhf/ftp/stobst.pdf

    Attributes:
        trees {list}: A list of RegressionTree objects.
        lr {float}: Learning rate.
        init_val {float}: Initial value to predict.
        fn {function}: A function wrapper for prediction.
    """

    def __init__(self):
        self.trees = None
        self.learning_rate = None
        self.init_val = None
        self.fn = lambda x: NotImplemented

    def _get_init_val(self, label: array):
        """Calculate the initial prediction of y.

        Arguments:
            label {array} -- Target values.

        Returns:
            NotImplemented
        """

        return NotImplemented

    @staticmethod
    def _match_node(row: array, tree: RegressionTree) -> Node:
        """Find the leaf node that the sample belongs to.

        Arguments:
            row {array} -- Sample of training data.
            tree {RegressionTree}

        Returns:
            Node
        """

        node = tree.root
        while node.left and node.right:
            if row[node.feature] < node.split:
                node = node.left
            else:
                node = node.right
        return node

    @staticmethod
    def _get_leaves(tree: RegressionTree) -> list:
        """Gets all leaf nodes of a regression tree.

        Arguments:
            tree {RegressionTree}

        Returns:
            list -- A list of RegressionTree objects.
        """

        nodes = []
        que = [tree.root]
        while que:
            node = que.pop(0)
            if node.left is None or node.right is None:
                nodes.append(node)
                continue

            que.append(node.left)
            que.append(node.right)

        return nodes

    def _divide_regions(self, tree: RegressionTree, nodes: list,
                        data: array) -> Dict[Node, List[int]]:
        """Divide indexes of the samples into corresponding leaf nodes
        of the regression tree.

        Arguments:
            tree {RegressionTree}
            nodes {list} -- A list of Node objects.
            data {array} -- Training data.

        Returns:
            Dict[Node, List[int]]-- e.g. {node1: [1, 3, 5], node2: [2, 4, 6]...}
        """

        regions = {node: [] for node in nodes}  # type: Dict[Node, List[int]]
        for i, row in enumerate(data):
            node = self._match_node(row, tree)
            regions[node].append(i)

        return regions

    def _get_residuals(self, label: array, prediction: array) -> array:
        """Update residuals for each iteration.

        Arguments:
            label {array} -- Target values.
            prediction {array} -- Prediction of label.

        Returns:
            array -- residuals
        """

        return label - self.fn(prediction)

    def _update_score(self, tree:RegressionTree, data:array, prediction:array, residuals:array):
        """update the score of regression tree leaf node.

        Arguments:
            tree {RegressionTree}
            data {array} -- Training data.
            prediction {array} -- Prediction of label.
            residuals {array}
        """

        NotImplemented

    def fit(self, data: array, label: array, n_estimators: int, learning_rate: float,
            max_depth: int, min_samples_split: int, subsample=None):
        """Build a gradient boost decision tree.

        Arguments:
            data {array} -- Training data.
            label {array} -- Target values.
            n_estimators {int} -- number of trees.
            learning_rate {float} -- Learning rate.
            max_depth {int} -- The maximum depth of the tree.
            min_samples_split {int} -- The minimum number of samples required
            to split an internal node.

        Keyword Arguments:
            subsample {float} -- Subsample rate without replacement.
            (default: {None})
        """

        # Calculate the initial prediction of y.
        self.init_val = self._get_init_val(label)
        # Initialize prediction.
        n_rows = len(label)
        prediction = np.full(label.shape, self.init_val)
        # Initialize the residuals.
        residuals = self._get_residuals(label, prediction)

        # Train Regression Trees
        self.trees = []
        self.learning_rate = learning_rate
        for _ in range(n_estimators):
            # Sampling with replacement
            idx = range(n_rows)
            if subsample is not None:
                k = int(subsample * n_rows)
                idx = choice(idx, k, replace=True)
            data_sub = data[idx]
            residuals_sub = residuals[idx]
            prediction_sub = prediction[idx]

            # Train a Regression Tree by sub-sample of X, residuals
            tree = RegressionTree()
            tree.fit(data_sub, residuals_sub, max_depth, min_samples_split)

            # Update scores of tree leaf nodes
            self._update_score(tree, data_sub, prediction_sub, residuals_sub)
            # Update prediction
            prediction = prediction + learning_rate * tree.predict(data)
            # Update residuals
            residuals = self._get_residuals(label, prediction)

            self.trees.append(tree)

    def _predict(self, row: array) -> float:
        """Auxiliary function of predict.

        Arguments:
            row {array} -- A sample of training data.

        Returns:
            float -- Prediction of label.
        """

        # Sum prediction with residuals of each tree.
        residual = np.sum([self.learning_rate * tree._predict(row)
                           for tree in self.trees])

        return self.fn(self.init_val + residual)
