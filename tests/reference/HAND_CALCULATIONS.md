# How each reference value was computed by hand

These values were worked out with pencil-and-paper arithmetic before the code ran.
The tests in `tests/test_stats_reference.py` compare the code to them. Never change a value
here to make a test pass. Fix the code instead.

## Cohen's kappa, 2 by 2 table

|            | truth yes | truth no |
| ---------- | --------- | -------- |
| judge yes  | 20        | 5        |
| judge no   | 10        | 15       |

1. n = 20 + 5 + 10 + 15 = 50.
2. Observed agreement po = (20 + 15) / 50 = 35 / 50 = 0.7.
3. The judge says yes 25 times, so P(judge yes) = 25 / 50 = 0.5. P(judge no) = 0.5.
4. The truth is yes 30 times, so P(truth yes) = 30 / 50 = 0.6. P(truth no) = 0.4.
5. Chance agreement pe = 0.5 x 0.6 + 0.5 x 0.4 = 0.30 + 0.20 = 0.5.
6. kappa = (po - pe) / (1 - pe) = (0.7 - 0.5) / (1 - 0.5) = 0.2 / 0.5 = 0.4.

## Cohen's kappa, 3 labels

Pairs (rater 1, rater 2, count): (a,a,8) (a,b,2) (b,b,6) (b,c,2) (c,c,4) (c,a,3). n = 25.

1. po = (8 + 6 + 4) / 25 = 18 / 25 = 0.72.
2. Rater 1 marginals: a = 10, b = 8, c = 7 (out of 25).
3. Rater 2 marginals: a = 11, b = 8, c = 6.
4. pe = (10 x 11 + 8 x 8 + 7 x 6) / 25^2 = (110 + 64 + 42) / 625 = 216 / 625 = 0.3456.

   Check by rows: a: 10/25 x 11/25 = 0.176, b: 8/25 x 8/25 = 0.1024, c: 7/25 x 6/25 = 0.0672.
   Sum = 0.3456.


5. kappa = (0.72 - 0.3456) / (1 - 0.3456) = 0.3744 / 0.6544 = 0.5721271...

## pass@k, unbiased formula 1 - C(n-c, k) / C(n, k)

- n=5, c=2, k=1: C(3,1)=3, C(5,1)=5. 1 - 3/5 = 0.4.
- n=5, c=2, k=2: C(3,2)=3, C(5,2)=10. 1 - 3/10 = 0.7.
- n=5, c=2, k=3: C(3,3)=1, C(5,3)=10. 1 - 1/10 = 0.9.
- n=5, c=2, k=4: n - c = 3 < k = 4, so every set of 4 samples holds a correct one. Value 1.0.
- n=4, c=0, k=2: C(4,2)/C(4,2) = 1. 1 - 1 = 0.0.
- n=4, c=4, k=2: n - c = 0 < 2. Value 1.0.
- n=10, c=3, k=5: C(7,5)=21, C(10,5)=252. 1 - 21/252 = 1 - 1/12 = 11/12 = 0.916666...

## Mean and standard error (sample standard deviation, ddof = 1)

Values 1, 0, 1, 1, 0, 1, 1, 1. n = 8.

1. Mean = 6 / 8 = 0.75.
2. Deviations: six values of +0.25 and two of -0.75.
3. Sum of squares = 6 x 0.0625 + 2 x 0.5625 = 0.375 + 1.125 = 1.5.
4. Sample variance = 1.5 / (8 - 1) = 0.2142857...
5. Sample sd = sqrt(0.2142857) = 0.4629100...
6. SE = 0.4629100 / sqrt(8) = 0.4629100 / 2.8284271 = 0.1636634...

## Paired difference

a = 1, 1, 0, 1, 0 and b = 1, 0, 0, 1, 1. d = a - b = 0, 1, 0, 0, -1.

1. Mean of d = 0 / 5 = 0.
2. Sample variance of d = (0 + 1 + 0 + 0 + 1) / 4 = 0.5.
3. Paired SE = sqrt(0.5 / 5) = sqrt(0.1) = 0.3162277...
4. Unpaired SE: a has mean 0.6. Its deviations are 0.4, 0.4, -0.6, 0.4, -0.6.
   The squares sum to 0.16 x 3 + 0.36 x 2 = 1.2, so the sample variance is 1.2 / 4 = 0.3.
   b holds the same values in another order, so its variance is 0.3 too.
   SE_a^2 = 0.3 / 5 = 0.06, SE_b^2 = 0.06. Unpaired SE = sqrt(0.12) = 0.3464101...

## Bootstrap

- Repeatability: two calls with seed 1 must return the same interval to the last bit.
- A Bernoulli sample with 300 ones in 1000 has p = 0.3. The normal interval is
  0.3 +/- 1.959964 x sqrt(0.3 x 0.7 / 1000) = 0.3 +/- 1.959964 x 0.0144914 = 0.3 +/- 0.0284030,
  so [0.2715970, 0.3284030]. The percentile bootstrap interval must sit within 0.01 of each end.
  The tolerance is about 1/3 of the half width. This is a sanity bound, not an exact value.
