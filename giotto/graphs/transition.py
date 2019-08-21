# Authors: Guillaume Tauzin <guillaume.tauzin@epfl.ch>
#          Umberto Lupo <u.lupo@l2f.ch>
# License: TBD

import numpy as np
from sklearn.utils._joblib import Parallel, delayed
from scipy import sparse as sp
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.utils.validation import check_is_fitted


class TransitionGraph(BaseEstimator, TransformerMixin):
    """Given a collection of two-dimensional arrays, with row :math:`i` in
    array :math:`A` encoding the "state" of a system at "time" :math:`i`,
    this transformer returns a corresponding collection of so-called
    *transition graphs*. The vertex set of graph :math:`G` corresponding to
    :math:`A` is the set of all unique rows (states) in :math:`A`, and there
    is an edge between two vertices if and only if one of the two rows
    immediately follows the other anywhere in :math:`A`.

    Parameters
    ----------
    n_jobs : int or None, optional, default: None
        The number of jobs to use for the computation. ``None`` means 1 unless
        in a :obj:`joblib.parallel_backend` context. ``-1`` means using all
        processors.

    Examples
    --------
    >>> from giotto.graphs import TransitionGraph
    >>> dyn = np.array([[['a'], ['b'], ['c']],
    ...                 [['c'], ['a'], ['b']])
    >>> tg = TransitionGraph()
    >>> tg.fit_transform(dyn)

    """

    def __init__(self, n_jobs=None):
        self.n_jobs = n_jobs

    def get_params(self, deep=True):
        """Get parameters for this estimator.

        Parameters
        ----------
        deep : boolean, optional, default: True
            Behaviour not yet implemented.

        Returns
        -------
        params : mapping of string to any
            Parameter names mapped to their values.
        """
        return {'n_jobs': self.n_jobs}

    @staticmethod
    def _validate_params():
        """A class method that checks whether the hyperparameters and the
        input parameters of the :meth:'fit' are valid.
        """
        pass

    def _make_adjacency_matrix(self, X):
        indices = np.unique(X, axis=0, return_inverse=True)[1]
        n_indices = 2 * (len(indices) - 1)
        first = indices[:-1]
        second = indices[1:]
        A = sp.csr_matrix((np.full(n_indices, True),
                           (np.concatenate([first, second]),
                            np.concatenate([second, first]))),
                          dtype=bool)
        sp.csr_matrix.setdiag(A, 0)
        return A

    def fit(self, X, y=None):
        """Do nothing and return the estimator unchanged.
        This method is just there to implement the usual API and hence
        work in pipelines.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_time_steps, n_features)
            Input data.

        y : None
            There is no need of a target in a transformer, yet the pipeline API
            requires this parameter.

        Returns
        -------
        self : object
            Returns self.
        """
        self._validate_params()

        self._is_fitted = True
        return self

    def transform(self, X, y=None):
        """Create transition graphs from the input data and return their
        adjacency matrices. The graphs are simple, undirected and
        unweighted, and the adjacency matrices are sparse matrices of type
        bool.

        Parameters
        ----------
        X : ndarray, shape (n_samples, n_time_steps, n_features)
            Input data.

        y : None
            There is no need of a target in a transformer, yet the pipeline API
            requires this parameter.

        Returns
        -------
        X_transformed : array of sparse boolean matrices, shape (n_samples, )
            The collection of ``n_samples`` transition graphs. Each transition
            graph is encoded by a sparse matrix of boolean type.
        """
        # Check is fit had been called
        check_is_fitted(self, ['_is_fitted'])

        n_samples = X.shape[0]

        X_transformed = Parallel(n_jobs=self.n_jobs)(
            delayed(self._make_adjacency_matrix)(X[i]) for i in
            range(n_samples))
        X_transformed = np.array(X_transformed)
        return X_transformed