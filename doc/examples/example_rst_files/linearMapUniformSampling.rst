.. _linearMap:


===========================
Example: Linear Map with Uniform Sampling
===========================

We will wailk through the following `example
<https://github.com/UT-CHG/BET/blob/master/examples/linearMap/linearMapUniformSampling.py>`_. This example
generates uniform samples in a 3D input parameter space and evaluates a 
linear map to a 2D data space. The stochastic inverse problem solved here
is one of parameter identification under uncertainty. A reference parameter
is defined for which a reference datum is computed. A probability measure
is then defined around this reference datum and this probability measure
is inverted using a non-intrusive measure-theoretic algorithm. 
Probabilities in the parameter space are 
calculated using emulated points.  1D and 2D marginals are calculated,
smoothed, and plotted.

Import the necessary modules::

    import numpy as np
    import bet.calculateP as calculateP
    import bet.postProcess as postProcess
    import bet.calculateP.simpleFunP as simpleFunP
    import bet.calculateP.calculateP as calculateP
    import bet.postProcess.plotP as plotP

Define the parameter domain and reference parameter::

  lam_domain= np.array([[0.0, 1.0],
		    [0.0, 1.0],
		    [0.0, 1.0]])

  ref_lam = [0.5, 0.5, 0.5]
Suggested changes for user (1)
------------------------------

Try setting ``n0``, ``n1``, and ``n2`` all to 10 and compare the results. Also, we can do uniform random sampling by setting:: 

  random_sample = True
  
If ``random_sample = True``, consider defining::
   
  n_samples = 1E3
        
Then also try ``n_samples = 1E4``. What happens when ``n_samples = 1E2``?

Define sampling types random or regular::

  random_sample = True

  if random_sample == False:
    n0 = 30 # number of samples in lam0 direction
    n1 = 30 # number of samples in lam1 direction
    n2 = 30 # number of samples in lam2 direction
    n_samples = n0*n1*n2
  else:
    n_samples = 2E3  


Set up the samples::

  if random_sample == False:
    vec0=list(np.linspace(lam_domain[0][0], lam_domain[0][1], n0))
    vec1 = list(np.linspace(lam_domain[1][0], lam_domain[1][1], n1))
    vec2 = list(np.linspace(lam_domain[2][0], lam_domain[2][1], n2))
    vecv0, vecv1, vecv2 = np.meshgrid(vec0, vec1, vec2, indexing='ij')
    samples=np.vstack((vecv0.flat[:], vecv1.flat[:], vecv2.flat[:])).transpose()
  else:
    samples = calculateP.emulate_iid_lebesgue(lam_domain=lam_domain, 
					      num_l_emulate = n_samples)      
      
Define the QoI map::

  Q_map = np.array([[0.506, 0.463],[0.253, 0.918], [0.085, 0.496]])

Define the reference QoI::
    
  Q_ref =  np.array([0.422, 0.9385])


Calculate and save the data.::

  data= np.dot(samples,Q_map)
  np.savetxt('3to2_samples.txt.gz', samples)
  np.savetxt('3to2_data.txt.gz', data)

Note that saving the data as shown above
implies that all of the above code can be skipped in the future. Given files
containing the parameter samples and associated QoI data from a computational model, 
we can simply read in the arrays and solve the stochastic inverse problem
as shown below. 
  
Suggested changes for user (2)
------------------------------

Try different ways of discretizing the probability measure on
:math:`\mathcal{D}` defined as a uniform probability measure on a rectangle
(since :math:`\mathcal{D}` is 2-dimensional).
    
*   unif_unif creates a uniform measure on a hyperbox with dimensions relative   to the size of the circumscribed hyperbox of the set :math:`\mathcal{D}`  using the bin_ratio. A total of M samples are drawn within a slightly larger  scaled hyperbox to discretize this measure defining M total generalized  contour events in Lambda.  The reason a slightly larger scaled hyperbox is  used to draw the samples to discretize :math:`\mathcal{D}` is because  otherwise every generalized contour event will have non-zero probability  which obviously defeats the purpose of "localizing" the probability within a  subset of :math:`\mathcal{D}`.
    
*   uniform_hyperrectangle uses the same measure defined in the same way as  unif_unif, but the difference is in the discretization which is on a regular  grid defined by ``center_pts_per_edge``.  If ``center_pts_per_edge = 1``,  then the contour event corresponding to the entire support of  :math:`\rho_\mathcal{D}` is approximated as a single event. This is done by  carefully placing a regular 3x3 grid (since :math:`dim(\mathcal{D})=2` in this  case) of points in :math:`\mathcal{D}` with the center point of the grid in  the center of the support of the measure and the other points placed outside  of the rectangle defining the support to define a total of 9 contour events  with 8 of them having exactly zero probability.

Create a simple function approximation of the probablity measure on
:math:`\mathcal{D}`::

    deterministic_discretize_D = True

    if deterministic_discretize_D == True:
      (d_distr_prob, d_distr_samples, d_Tree) = simpleFunP.uniform_hyperrectangle(data=data,
                                                  Q_ref=Q_ref, bin_ratio=0.2, center_pts_per_edge = 1)
    else:
      (d_distr_prob, d_distr_samples, d_Tree) = simpleFunP.unif_unif(data=data,
                                                  Q_ref=Q_ref, M=50, bin_ratio=0.2, num_d_emulate=1E5)

Suggested changes for user (3)
------------------------------

If using a regular grid of sampling (if ``random_sample = False``), we set::
    
  lambda_emulate = samples
  
Otherwise, play around with num_l_emulate. A value of 1E2 will probably
give poor results while results become fairly consistent with values 
that are approximately 10x the number of samples.
   
Note that you can always use::
    
  lambda_emulate = samples
        
and this simply will imply that a standard Monte Carlo assumption is
being used, which in a measure-theoretic context implies that each 
Voronoi cell is assumed to have the same measure. This type of 
approximation is more reasonable for large ``n_samples`` due to the slow 
convergence rate of Monte Carlo (it converges like 1/sqrt(``n_samples``)).

Set up volume emulation::

    if random_sample == False:
      lambda_emulate = samples
    else:
      lambda_emulate = calculateP.emulate_iid_lebesgue(lam_domain=lam_domain, num_l_emulate = 1E5)


Calculate probablities::

    (P,  lambda_emulate, io_ptr, emulate_ptr) = calculateP.prob_emulated(samples=samples,
                                                                         data=data,
                                                                         rho_D_M=d_distr_prob,
                                                                         d_distr_samples=d_distr_samples,
                                                                         lambda_emulate=lambda_emulate,
                                                                         d_Tree=d_Tree)

                                                                                                                                                  
Calculate 2D marginal probs  - Suggested changes for user (4)
-------------------------------------------------------------
    
At this point, the only thing that should change in the plotP.* inputs
should be either the nbins values or sigma (which influences the kernel
density estimation with smaller values implying a density estimate that
looks more like a histogram and larger values smoothing out the values
more).
    
There are ways to determine "optimal" smoothing parameters (e.g., see CV, GCV,
and other similar methods), but we have not incorporated these into the code
as lower-dimensional marginal plots have limited value in understanding the
structure of a high dimensional non-parametric probability measure.

Plot the marginal probabilities::

    (bins, marginals2D) = plotP.calculate_2D_marginal_probs(P_samples = P, samples = lambda_emulate, lam_domain = lam_domain, nbins = [10, 10, 10])

Smooth 2d marginals probs (optional)::

    marginals2D = plotP.smooth_marginals_2D(marginals2D,bins, sigma=0.1)

Plot 2d marginals probs::

    plotP.plot_2D_marginal_probs(marginals2D, bins, lam_domain, filename = "linearMap",
                             plot_surface=False)

Calculate 1d marginal probs::

    (bins, marginals1D) = plotP.calculate_1D_marginal_probs(P_samples = P, samples = lambda_emulate, lam_domain = lam_domain, nbins = [10, 10, 10])

Smooth 1d marginal probs (optional)::

    marginals1D = plotP.smooth_marginals_1D(marginals1D, bins, sigma=0.1)

Plot 1d marginal probs::

    plotP.plot_1D_marginal_probs(marginals1D, bins, lam_domain, filename = "linearMap")





