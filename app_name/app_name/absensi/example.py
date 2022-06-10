
"""

This script implements a multilateration algorithm that, given the coordinates of a finite number of radio stations,
and given their distances to the station (derived from the intensities of the signal they received in a previous step)
computes the most probable coordinates of the station. Even if the distances computed for each station do not match
(in terms of pointing to a single optimal solution) the algorithm finds the coordinates that minimize the error function
and returns the most optimal solution possible.


https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
https://docs.scipy.org/doc/scipy/reference/optimize.minimize-neldermead.html#optimize-minimize-neldermead

"""

from scipy.optimize import minimize
import numpy as np

def gps_solve(distances_to_station, stations_coordinates):
	def error(x, c, r):
		# print(x)
		return sum([(np.linalg.norm(x - c[i]) - r[i]) ** 2 for i in range(len(c))])

	l = len(stations_coordinates)
	S = sum(distances_to_station)
	# compute weight vector for initial guess
	W = [((l - 1) * S) / (S - w) for w in distances_to_station]
	print(W)
	# get initial guess of point location
	x0 = sum([W[i] * stations_coordinates[i] for i in range(l)])
	# print(x0)
	# optimize distance from signal origin to border of spheres
	return minimize(error, x0, args=(stations_coordinates, distances_to_station), method='Nelder-Mead').x


if __name__ == "__main__":
	antena0 = [43,45]
	antena1 = [44,-47]
	antena2 = [-46,-48]
	antena3 = [-39,40]
	distance0 = 0
	distance1 = 90.630
	distance2 = 53.231
	distance3 = 69.360

	stations = list(np.array([antena1, antena2, antena3]))
	distances_to_station = [distance1, distance2, distance3]
	# distances_to_station = [distance0, distance1, distance2, distance3]

	# print(gps_solve(distances_to_station, stations))