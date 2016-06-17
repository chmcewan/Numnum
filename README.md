# Numnum

Numnum is a library to simplify and improve testing numerical algorithms. It simplifies testing by removing the need to generate boilerplate unit and integration test suites. It improves testing by being more thorough in its exploration and more accurate in its comparisons. 

It is particularly useful for validating Matlab prototypes that have been ported into Python software.

## Basic principles

The main idea behind Numnum is to "record" executions of an algorithm in a way that can be "replayed" at a later date. Literally,

	>> Numnum.record('test1.mat', @my_algorithm, ...)

will gather information on function invocation, input arguments and return values in a manner that can be recalled later. This makes it very easy to generate a large collection of test data automatically, rather than a small collection of hand-crafted test cases. Correspondingly,

	>> Numnum.replay('test1.mat')

will, by default, attempt to reproduce each function invocation individually (unit tests) and the entire execution (integration test). This ensures that numerical results are being preserved both locally and globally. A specific function can be unit tested against all recorded invocations with

	>> Numnum.replay('test1.mat', 'some_function')
	some_function: 100% (237 / 237)

The "trick" to getting this to work is instrumenting all functions that one cares to validate. Currently, this is an explicitly manual process, which is a little laborious but is the most expressive and flexible e.g.

	function [x, y, x] = some_function(a, b, c)
		Numnum.arguments('a', 'b', 'c')

		...

		Numnum.returns('x', 'y', 'z')
	end

Variable length input and output arguments, renaming variables and recording intermediate values are all supported. Numnum also provides random number generation that ensures determinism, even between languages. For example,

	vals = Numnum.randn(1000, 1)

When Numnum is not recording or replaying, then all of these functions are either no-ops or facades and should have no obvious effect on algorithm behaviour or performance.

