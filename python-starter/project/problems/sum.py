# from project.problem import Problem
# import argparse
#
# class SumProblem(Problem):
#
#     def initialize_parser(self, parser: argparse.ArgumentParser):
#         """
#         Initialize the parser with the necessary arguments
#         """
#         parser.add_argument('--sum', help='sum the given numbers', action='store_true')
#
#     def is_chosen_problem(self, args):
#         """
#         Check if the problem is chosen
#         """
#         return bool(args.sum)
#
#     def run(self, args):
#         """
#         Run the program
#         """
#         # Access the input and output file paths
#         input_file = args.input
#         output_file = args.output
#
#         # Read the numbers
#         with open(input_file, 'r') as f:
#             data = f.read()
#
#         numbers = data.split(',')
#         numbers = [int(number) for number in numbers]
#
#         # Process the numbers
#         result = sum(numbers)
#
#         # Write the result into the file
#         with open(output_file, 'w') as f:
#             f.write(str(result))
