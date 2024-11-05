import itertools
import numpy as np
import pandas
import types

# import Packs.DataGrid



def FindWeight(xarr, x):
	'''
	Purpose:
		FindWeight() assesses an array, looking for two values close to
		an input value x. It then finds the weights for those two values which
		allow it to approximate x. Finally, it returns the indicies and weights
		for those two array values.
	Input:
		x			:	(float)
						A value in the range [xarr[0],xarr[-1]] to be approximated
						by items in xarr
		xarr		:	(list(float))
						An array of values, which will be used to approximate x
	Output:
		[ [], [] ]	:	(list(list(int,float)))
						A pair of lists. Each list contains two values: an index
						in xarr (integer) and a weight for that index (float).
	Exceptions:
		'Failed: 0'	:	Indicates that the input x is not in the range covered by
						the input xarr.
		'Failed: 1'	:	Indicates that for some reason (excluding Failed: 0) the
						program was unable to find useful indicies in xarr.
	'''

	# print(x,xarr)
	# First, make sure x is in xarr's scope.
	if type(x) == type('string'): # String handling
		try:
			x1ind = xarr.index(x)
		except Exception as errorname: # Exception handling
			print(errorname)
			raise Exception('FindWeight(): Failed 0.1: Input x {} not in xarr {}.'.format(x,xarr))
		
		x1weight = 1.0 # Strings are assumed to be boolean-style weighted.
		return [ [x1ind, x1weight],[0,0] ]

	else:
		if x < min(xarr) or x > max(xarr): # Exception handling
			raise Exception('FindWeight(): Failed 0.2: Input x {} not in xarr {}.'.format(x,xarr))

		# Now, we handle situations where there is only one choice of variable.
		if len(xarr) == 1:
			return[ [0,1],[0,0] ]


		# Moving on, we now find x1 and x2, the two adjacent known values.
		x1 = 0
		x2 = 0
		for i in range(len(xarr)):
			if (xarr[i] == x): # On-grid point
				return [ [i, 1],[i, 0] ]
			elif (xarr[i] < x) and (xarr[i+1] > x): # Off-grid point
				x1ind = i
				x2ind = i+1

		# Lets make sure we found something.
		if x1ind == x2ind and x1ind == 0:
			raise Exception('FindWeight(): Failed 1: Unable to find indicies.')
		
		# Next, we calculate weights.
		x1weight = 1 - (x - xarr[x1ind])/(xarr[x2ind]-xarr[x1ind])
		x2weight = (x - xarr[x1ind])/(xarr[x2ind]-xarr[x1ind])

		# Now we can return the values, in short lists:
		return [ [x1ind, x1weight],[x2ind,x2weight] ]




def WeightAll(Xknown, xvalues):
	'''
	Purpose:
		WeightAll() iterates through an array of values corresponding to a set of
		N parameters. For each array element, it calls FindWeight() on the appropriate
		set of known parameter values; this creates an Nx2x2 tensor, which is the output
		of this function.
	Input:
		Xknown 		:	(list(list(float)))
						A two-dimensional array. The first dimension must span each of
						the N parameters. The second dimension must contain the "known"
						values for each individual parameters.
		xvalues		:	(list(float))
						A one-dimensional array. Each element is a value for a parameter
						which corresponds to the first dimension in Xknown; i.e. xvalues[i]
						is the value for the i-th parameter in Xknown. Note that exceptions
						will be thrown down the line if xvalues[i] is not between
						Xknown[i][0] and Xknown[i][-1].
	Output:
		Tensor		:	(list(list(list(int, float))))
						An Nx2x2 tensor. For each of the N parameters, Tensor contains
						the indicies and appropriate weightings of two known values to
						approximate the input parameter from xvalues.
	Exceptions:
		None
	'''

	# Prepare our output tensor for filling
	Tensor = [ [ [],[] ] for _ in range(len(xvalues)) ]

	for i in range(len(xvalues)): # Page through our parameter list...
		if xvalues[i] in Xknown[i] or type(xvalues[i]) == type('string'): # Addressing string and on-grid data calls.
			iindex = [ k for k in range(len(Xknown[i])) if Xknown[i][k] == xvalues[i] ][0]
			Tensor[i] = [ [ iindex, 1 ], [0,0] ] 
		else:
			Tensor[i] = FindWeight(Xknown[i],xvalues[i]) # filling our tensor as we go

	# Tensor should now contain, for each parameter, two indicies with weights.
	# Thus it's ready to return.
	return Tensor




def multipolateData(Tensor, dataFetcher):
	'''
	Purpose:
		MultipolateData() turns a set of indicies and weights, and a grid of models,
		into an output model approximation.
	Input:
		Tensor		:	(list(list(list(int, float))))
						An Nx2x2 tensor. For each of the N parameters, Tensor contains
						the indicies and appropriate weightings of two known values to
						approximate the input parameter from xvalues.
		Grid		:	numpy ndarray
						This is an (N+1)-dimensional cube. Each combination of the N
						parameters corresponds to a 1- or 2-dimensional model. Notes:
						If using 2-dimensional models, dimension 0 of these models should
						correspond to the x-axis. Otherwise, you must pass the x-axis
						into this function as the 'dimension' variable.
		gridType	:	string
						Describes the type of data grid. Must be one of: 'Data', for a grid containing
						actual data; 'Pointers', for a grid containing filenames; or 'DataGrid', for
						a DataGrid-class object as defined above.
	Output:
		InterpData	:	numpy array
						A 2-dimensional array representing the interpolated model grid.
	Exceptions:
	'''

	inputModels = [] # Initializing the set of models which will be interpolated

	weightGrid = [] # Initializing a grid which will contain weights for inputModels

	buildIterations = [ range(2) for _ in range(len(Tensor)) ]  # Calculate all possible arrangements
	allIterations = itertools.product(*buildIterations) 		# of high/low within our parameter space

	locationList = []

	for iteration in allIterations: # Paging through each of these to find their weights
		
		modelWeight = 1 # Initialize this model's weight

		for j in range(len(iteration)): # Each "iteration" is a sequence of weights. So, find each weight...
			
			modelWeight = modelWeight * Tensor[j][iteration[j]][1] # ...and combine them together.

		if modelWeight == 0: 
			continue # This model has no weight. Do not waste time loading it, continue the next.

		weightGrid.append(modelWeight) # We have the weight for this model; store for later use.

		# Fetch this model
		modelLocation = [ Tensor[j][iteration[j]][0] for j in range(len(iteration)) ]
		result = dataFetcher(modelLocation)

		# Add the model associated with this iteration to inputModels
		locationList.append( modelLocation )
		inputModels.append( result )

	# Each item in weightGrid corresponds to an item in allIterations. Thus, we can now combine the weights
	# and the models to produce the final model.

	dimension = inputModels[0][0]

	for i in range(len(inputModels)):
		size = len(inputModels[i][0])
		if size != len(dimension):
			Exception('Error: multipolateData() Failed 0: Mismatched grid sizes.')
			print('bad length:')
			print(locationList[0])
			print(locationList[i])
			return np.array([dimension,np.zeros(len(dimension))])

		else:
			continue


	outputModel = np.zeros(len(dimension)) # Initializing our multipolated output grid.	

	for i in range(len(dimension)): # Building up our output, one x-value at a time
		# For each x-value, the output will be the sum of that x-value for each input model,
		# multiplied by that model's weight.
		for j in inputModels:
			if dimension[i] != j[0][i]:
				Exception('Error: multipolateData() Failed 1: Grid indicies do not agree.')
				print('bad scaling')

				return np.array([dimension,np.zeros(len(dimension))])
			else:
				continue

		outputModel[i] = np.sum([ inputModels[j][-1][i] * weightGrid[j] for j in range(len(inputModels)) ])

	InterpData = np.array([dimension, outputModel]) # Arrange our final product in to an x,y array
	
	# The output grid is now ready to be returned.
	return InterpData




def SingleCallMP(Xknown, xvalues, dataFetcher):
	'''
	Purpose:
		This function is a shortcut, which allows to call both WeightGrid and MultipolateData with a single function call.
	Input:
		Xknown		:	A 2-dimensional list (list of lists) spanning the dimensionality of the database of models to be interpolated.
						Dimension 0 should have a length equal to the number of dimensions, with each index representing a parameter.
						Dimension 1 should contain the valid values for each parameter.
		xvalues		:	A list containing the values for each parameter, for which we are attempting to approximate. The indicies of
						the parameter values should match with the indicies in Xknown.
		dataFetcher	:	A function which accepts a list-like of index values keyed to represent values in Xknown, and which returns a
						2-dimensional list-like of x, y values representing a model.
	Output:
		Output		:	A 2-dimensional array of x, y values approximating the desired model.
	'''
	#
	if type(dataFetcher) != types.FunctionType:
		print('You must pass a dataFetcher function.')
		raise Exception

	Tensor = WeightAll(Xknown,xvalues) # Retrieve the models and weights.
	Output = multipolateData(Tensor, dataFetcher = dataFetcher) # Calculate the multipolated output.

	# Return the result.
	return(Output)




# Changelog
# 04/17/20: Bugfixes: SingeCallMP variables, and a syntax error on line 45. -ASmith
# 04/15/20: Continued working on yesterday's project. -Asmith
#			Implemented arbitrary "dataFetcher" functionality: pass a dataFetcher() function a list of indexes and expect back a 2d array of values. -Asmith
#			Added a flag to completely skip zero-weight models. This greatly speeds up the multipolation. -Asmith
#			Various related bugfixing as well. -Asmith
# 04/14/20: Started working on a more user-friendly data fetching scheme. -Asmith
# 11/8/19: Corrected a bug that would cause a crash when searching for the last element in any dimension -Asmith
# 10/8/19: Additional type handling corrections -Asmith
# 9/25/19: Additional handling of strings -Asmith
# 9/24/19: Added handling of strings (boolean-type variables) -Asmith
# 9/23/19: Temporary bugfix to throw an exception and quit if the data does not match in dimension 0. -Asmith
#			Additionally, added some comments. -Asmith
# 9/5/19: Wrote SinglecallMP(). -Asmith
# 8/30/19: Combined the multipolation functions -Asmith
#			Started changelog -Asmith