# Lindley Graham 4/15/2014
"""
This module contains functions for sampling. We assume we are given access to a
model, a parameter space, and a data space. The model is a map from the
paramter space to the data space. We desire to build up a set of samples to
sovle an inverse problem this guving use information about the inverse mapping.
Each sample consists for a paramter coordinate, data coordinate pairing. We
assume the measure on both spaces in Lebesgue.
"""

import numpy as np
import scipy as sio
from pyDOE import lhs
import matplotlib.pyplot as plt

def in_high_prob(data, rho_D, maximum, sample_nos=None):
    """
    Estimates the number of samples in high probability regions of D.

    :param data: Data associated with ``samples``
    :type data: :class:`np.ndarray`
    :param rho_D: probability density on D
    :type rho_D: callable function that takes a :class:`np.array` and returns a
        :class:`np.ndarray`
    :param list sample_nos: sample numbers to plot

    """
    if sample_nos==None:
        sample_nos = range(data.shape[0])
    rD = rho_D(data[sample_nos,:])
    print "Samples in box "+str(int(sum(rD)/maximum))

def in_high_prob_multi(results_list, rho_D, maximum, sample_nos_list=None):
    """
    Estimates the number of samples in high probability regions of D for a list of results.

    :param list results_list: list of (results, data) tuples
    :param rho_D: probability density on D
    :type rho_D: callable function that takes a :class:`np.array` and returns a
        :class:`np.ndarray`
    :param list sample_nos_list: list of sample numbers to plot (list of lists)

    """
    if sample_nos_list:
        for result, sample_nos in zip(results_list, sample_nos_list):
            in_high_prob(result[1], rho_D, maximum, sample_nos)
    else:
        for result in results_list:
            in_high_prob(result[1], rho_D, maximum)

def loadmat(save_file, model = None):
    """
    Loads data from ``save_file`` into a
    :class:`~polysim.run_framework.adaptive_samplers.adaptiveSamples` object.

    :param string save_file: file name
    :param model: runs the model at a given set of parameter samples and returns data
    :rtype: tuple
    :returns: (sampler, samples, data)

    """
    # load the data from a *.mat file
    mdat = sio.loadmat(save_file)
    # load the samples
    if mdat.has_key('samples'):
        samples = mdat['samples']
    else:
        samples = None
    # load the data
    if mdat.has_key('data'):
        data = mdat['data']
    else:
        data = None
    sampler = basic(mdat['num_samples'], None)    
    return (sampler, samples, data)

class sampler(object):
    """
    This class provides methods for adaptive sampling of parameter space to
    provide samples to be used by algorithms to solve inverse problems. 

    num_samples
        total number of samples OR list of number of samples per dimension such
        that total number of samples is prob(num_samples)
    lb_model
        :class:`~bet.loadBalance.load_balance` runs the model at a given set of
        parameter samples and returns data 
    """
    def __init__(self, lb_model, num_samples=None):
        """
        Initialization
        """
        self.num_samples = num_samples
        self.lb_model = lb_model

    def save(self, mdict, save_file):
        """
        Save matrices to a ``*.mat`` file for use by ``MATLAB BET`` code and
        :meth:`~bet.sampling.loadmat`

        :param dict() mdict: dictonary of sampling data and sampler parameters
        :param string save_file: file name

        """
        sio.savemat(save_file, mdict, do_compression=True)

    def update_mdict(self, mdict):
        """
        Set up references for ``mdict``

        :param dict() mdict: dictonary of sampler parameters

        """
        mdict['num_samples'] = self.num_samples
 
    def _plot_2D(self, samples, sample_nos, rD, p_true, save, show,
            xlabel, ylabel, filename):
        if sample_nos==None:
            sample_nos = range(samples.shape[1])
        rD = rD[sample_nos]
        plt.scatter(samples[0,sample_nos],samples[1,sample_nos],c=rD,
                cmap=plt.cm.Oranges_r)
        plt.colorbar()
        if p_true != None:
            plt.scatter(p_true[0], p_true[1], c='b')
        if save:
            plt.autoscale(tight=True)
            plt.xlabel(xlabel)
            plt.ylabel(ylabel)
            plt.savefig(filename, bbox_inches='tight', transparent=True,
                    pad_inches=0)
        if show:
            plt.show()
        else:
            plt.close()
       
    def show_param_2D(self, samples, data, rho_D = None, p_true=None,
            sample_nos=None, save=True, show=True):
        """
        Plot samples in parameter space and colors them either by rho_D or by
        sample batch number.

        :param samples: Samples to plot
        :type samples: :class:`np.ndarray`
        :param data: Data associated with ``samples``
        :type data: :class:`np.ndarray`
        :param list sample_nos: sample numbers to plot
        :param rho_D: probability density on D
        :type rho_D: callable function that takes a :class:`np.array` and returns a
            :class:`np.ndarray`
        :param p_true: true parameter value
        :type p_true: :class:`np.ndarray`

        """
       
        if rho_D!=None:
            rD = rho_D(data)
        xlabel = r'$\lambda_1$'
        ylabel = r'$\lambda_2$'
        savename = 'param_samples_cs.eps'
        self._plot_2D(samples, sample_nos, rD, p_true, save, show,
                xlabel, ylabel, savename)

    def show_data_2D(self, data, rho_D=None, Q_true=None, sample_nos=None,
            save=True, show=True):
        """
        Plot samples in data space and colors them either by rho_D or by
        sample batch number.

        :param data: Data associated with ``samples``
        :type data: :class:`np.ndarray`
        :param list sample_nos: sample numbers to plot
        :param rho_D: probability density on D
        :type rho_D: callable function that takes a :class:`np.array` and returns a
            :class:`np.ndarray`
        :param Q_true: true parameter value
        :type Q_true: :class:`np.ndarray`

        """   
        if rho_D!=None:
            rD = rho_D(data)
        xlabel = r'$q_1$'
        ylabel = r'$q_2$'
        savename = 'data_samples_cs.eps'
        self._plot_2D(data.transpose(), sample_nos, rD, Q_true,
                save, show, xlabel, ylabel, savename)

    def random_samples(self, sample_type, param_min, param_max,
            savefile, criterion='center'):
        """
        Sampling algorithm with three basic options

            * ``random`` (or ``r``) generates ``num_samples`` samples in
                ``lam_domain`` assuming a Lebesgue measure.
            * ``lhs`` generates a latin hyper cube of samples.

        Note: This function is designed only for generalized rectangles and
        assumes a Lebesgue measure on the parameter space.
       
        :param string sample_type: type sampling random (or r),
            latin hypercube(lhs), regular grid (rg), or space-filling
            curve(TBD) 
        :param param_min: minimum value for each parameter dimension
        :type param_min: np.array (ndim,)
        :param param_max: maximum value for each parameter dimension
        :type param_max: np.array (ndim,)
        :param t_kernel: method for creating new parameter steps using
            given a step size based on the paramter domain size
        :type t_kernel: :class:~`t_kernel`
        :param function heuristic: functional that acts on the data used to
            determine the proposed change to the ``step_size``
        :param string savefile: filename to save samples and data
        :param string criterion: latin hypercube criterion see 
            `PyDOE <http://pythonhosted.org/pyDOE/randomized.html>`_
        :rtype: tuple
        :returns: (``parameter_samples``, ``data_samples``) where
            ``parameter_samples`` is np.ndarray of shape (ndim, num_samples)
            and ``data_samples`` is np.ndarray of shape (num_samples, mdim)

        """
        # Create N samples
        param_left = np.repeat([param_min], self.num_samples,
                0).transpose()
        param_right = np.repeat([param_max], self.num_samples,
                0).transpose()
        samples = (param_right-param_left)
         
        if sample_type == "lhs":
            samples = samples * lhs(param_min.shape[0],
                    self.num_samples, criterion).transpose()
        elif sample_type == "random" or "r":
            samples = samples * np.random.random(param_left.shape) 
        samples = samples + param_left
        return self.user_samples(samples, savefile)

    def user_samples(self, samples, savefile):
        """
        Samples the model at ``samples`` and saves the results.

        Note: There are many ways to generate samples on a regular grid in
        Numpy and other Python packages. Instead of reimplementing them here we
        provide sampler that utilizes user specified samples.

        :param samples: samples to evaluate the model at
        :type samples: :class:`~numpy.ndarray` of shape (ndim, num_samples)
        :param string savefile: filename to save samples and data
        :rtype: tuple
        :returns: (``parameter_samples``, ``data_samples``) where
            ``parameter_samples`` is np.ndarray of shape (ndim, num_samples)
            and ``data_samples`` is np.ndarray of shape (num_samples, mdim)

        """
        
        # Update the number of samples
        self.num_samples = samples.shape[-1]

        # Solve the model at the samples
        data = self.lb_model(samples)

        mdat = dict()
        self.update_mdict(mdat)
        mdat['samples'] = samples
        mdat['data'] = data
        self.save(mdat, savefile)
        
        return (samples, data)

