# Task 2 explanation (verified and explained by Mingjiao Diao and Liuyixin Shao)

## What is the shape of the document matrix? Why must the question and document vectors have the same number of coordinates in a compatible space? Which operation turns six similarity scores into two selected passages?

The shape of the document matrix is `(6, 384)`. That means it has six rows, one for each passage, and each row has 384 coordinates. The question vector also has 384 coordinates, so we can multiply matching coordinates and add the products to calculate similarity. We then sort the six similarity scores and keep the top two. For Q1, they are A2 and T1.

## Find the largest and smallest coordinate among the displayed values. Can either number alone tell you what the passage means? Explain why the vector as a whole matters.

The largest displayed coordinate is `0.1357` at coordinate 12 of T1. The smallest is `-0.1167` at coordinate 5 of T1. Neither number alone tells us what T1 means because the coordinates work together to represent the passage. The vector as a whole matters because similarity depends on all 384 coordinates.
