# -*- coding: utf-8 -*-
"""
@Author: tushushu
@Date: 2018-07-05 17:51:04
@Last Modified by: tushushu
@Last Modified time: 2019-05-03 21:18:04
"""
from copy import copy
from ..utils.utils import list_split
import numpy as np
from numpy import array


class Node:
    """Node class to build tree leaves.

    Attributes:
        score {float} -- prediction of y (default: {None})
        left {Node} -- Left child node
        right {Node} -- Right child node
        feature {int} -- Column index
        split {int} --  Split point
    """

    def __init__(self, score=None):
        self.score = score
        self.left = None
        self.right = None
        self.feature = None
        self.split = None


class RegressionTree(object):
    """RegressionTree class.

    Attributes:
        root{Node}: the root node of DecisionTree
        depth{int}: the depth of DecisionTree
    """

    def __init__(self):
        self.root = Node()
        self.depth = 1
        self._rules = None

    def __str__(self):
        ret = []
        for i, rule in enumerate(self._rules):
            literals, score = rule
            ret.append("Rule %d: " % i, ' | '.join(
                literals) + ' => y_hat %.4f' % score)
        return ret

    @staticmethod
    def _expr2literal(expr):
        """Auxiliary function of print_rules.

        Arguments:
            expr {list} -- 1D list like [Feature, op, split]

        Returns:
            str
        """

        feature, operation, split = expr
        operation = ">=" if operation == 1 else "<"
        return "Feature%d %s %.4f" % (feature, operation, split)

    def _get_rules(self):
        """Get the rules of all the decision tree leaf nodes.
            Expr: 1D list like [Feature, op, split]
            Rule: 2D list like [[Feature, op, split], score]
            Op: -1 means less than, 1 means equal or more than
        """

        que = [[self.root, []]]
        self._rules = []
        # Breadth-First Search
        while que:
            node, exprs = que.pop(0)
            # Generate a rule when the current node is leaf node
            if not(node.left or node.right):
                # Convert expression to text
                literals = list(map(self._expr2literal, exprs))
                self._rules.append([literals, node.score])
            # Expand when the current node has left child
            if node.left:
                rule_left = copy(exprs)
                rule_left.append([node.feature, -1, node.split])
                que.append([node.left, rule_left])
            # Expand when the current node has right child
            if node.right:
                rule_right = copy(exprs)
                rule_right.append([node.feature, 1, node.split])
                que.append([node.right, rule_right])

    @staticmethod
    def _get_split_mse(col: array, score: array, split: float):
        """Calculate the mse of each set when x is splitted into two pieces.
        MSE as Loss fuction:
        y_hat = Sum(y_i) / n, i <- [1, n]
        Loss(y_hat, y) = Sum((y_hat - y_i) ^ 2), i <- [1, n]
        Loss = LossLeftNode + LossRightNode
        --------------------------------------------------------------------

        Arguments:
            col {array} -- A feature of training data.
            score {array} -- Target values.
            split {float} -- Split point of column.

        Returns:
            tuple -- MSE and average of splitted x
        """

        # Split score.
        score_left = score[col < split]
        score_right = score[col >= split]

        # Calculate the means of score.
        avg_left = score_left.mean()
        avg_right = score_right.mean()

        # Calculate the mse of score, D(X) = E{[X-E(X)]^2} = E(X^2)-[E(X)]^2.
        mse_left = (score_left ** 2).mean() - avg_left ** 2
        mse_right = (score_right ** 2).mean() - avg_right ** 2
        mse = mse_left + mse_right

        return mse, avg_left, avg_right

    def _choose_split(self, col: array, score: array):
        """Iterate each xi and split x, y into two pieces,
        and the best split point is the xi when we get minimum mse.

        Arguments:
            col {array} -- A feature of training data.
            score {array} -- Target values.

        Returns:
            tuple -- The best choice of mse, split point and average
        """
        # Feature cannot be splitted if there's only one unique element.
        unique = set(col)
        if len(unique) == 1:
            return None
        # In case of empty split
        unique.remove(min(unique))

        # Get split point which has min mse
        ite = map(lambda x: (x, *self._get_split_mse(col, score, x)), unique)
        split, mse, avg_left, avg_right = min(ite, key=lambda x: x[1])

        return split, mse, avg_left, avg_right

    def _choose_feature(self, data: array, score: array):
        """Choose the feature which has minimum mse.

        Arguments:
            data {array} -- Training data.
            score {array} -- Target values.

        Returns:
            tuple -- (feature number, split point, average)
        """

        # Compare the mse of each feature and choose best one.
        ite = map(lambda x: (x, *self._choose_split(
            data[:, x], score)), range(data.shape[1]))
        ite = filter(lambda x: x is not None, ite)

        # Terminate if no feature can be splitted
        return min(ite, default=None, key=lambda x: x[1])

    def fit(self, data: array, score: array, max_depth=5, min_samples_split=2):
        """Build a regression decision tree.
        Note:
            At least there's one column in X has more than 2 unique elements
            y cannot be all the same value

        Arguments:
            data {array} -- Training data.
            score {array} -- Target values.

        Keyword Arguments:
            max_depth {int} -- The maximum depth of the tree. (default: {5})
            min_samples_split {int} -- The minimum number of samples required
            to split an internal node (default: {2})
        """

        # Initialize with depth, node, indexes
        self.root.score = score.mean()
        que = [(self.depth + 1, self.root, data, score)]
        # Breadth-First Search
        while que:
            depth, node, _data, _score = que.pop(0)
            # Terminate loop if tree depth is more than max_depth
            if depth > max_depth:
                depth -= 1
                break
            # Stop split when number of node samples is less than
            # min_samples_split or Node is 100% pure.
            if _score.shape[0] < min_samples_split or all(_score == score[0]):
                continue
            # Stop split if no feature has more than 2 unique elements
            split_ret = self._choose_feature(_data, _score)
            if split_ret is None:
                continue
            # Split
            feature, split, avg_left, avg_right = split_ret
            # Update properties of current node
            node.feature = feature
            node.split = split
            node.left = Node(avg_left)
            node.right = Node(avg_right)
            # Put children of current node in que
            idx_left = (_data[:, feature] >= split)
            idx_right = (_data[:, feature] < split)
            que.append(
                (depth + 1, node.left, _data[idx_left], _score[idx_left]))
            que.append(
                (depth + 1, node.right, _data[idx_right], _score[idx_right]))
        # Update tree depth and rules
        self.depth = depth
        self._get_rules()

    def _predict(self, Xi):
        """Auxiliary function of predict.

        Arguments:
            Xi {list} -- 1D list with int or float

        Returns:
            int or float -- prediction of yi
        """

        nd = self.root
        while nd.left and nd.right:
            if Xi[nd.feature] < nd.split:
                nd = nd.left
            else:
                nd = nd.right
        return nd.score

    def predict(self, X):
        """Get the prediction of y.

        Arguments:
            X {list} -- 2d list object with int or float

        Returns:
            list -- 1d list object with int or float
        """

        return [self._predict(Xi) for Xi in X]
