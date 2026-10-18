# Appendix A: Machine Learning Project Checklist

## Core Idea
Géron's eight-step checklist turns any ML project into a repeatable process: frame, get data, explore, prepare, shortlist, fine-tune, present, launch. Ch 2 walks through it end to end. Adapt it to your needs, but **automate as much as possible** at every step and **never touch the test set until the end**.

## Frameworks Introduced
- **The 8 main steps**:
  1. Frame the problem and look at the big picture.
  2. Get the data.
  3. Explore the data to gain insights.
  4. Prepare the data to better expose the underlying patterns.
  5. Explore many different models and shortlist the best ones.
  6. Fine-tune your models and combine them into a great solution.
  7. Present your solution.
  8. Launch, monitor, and maintain your system.

## The Checklist (compact)

### 1. Frame the problem and look at the big picture
1. Define the objective in business terms.
2. How will your solution be used?
3. What are the current solutions/workarounds (if any)?
4. How should you frame the problem (supervised/unsupervised, online/offline, etc.)?
5. How should performance be measured?
6. Is the performance measure aligned with the business objective?
7. What would be the minimum performance needed to reach the business objective?
8. What are comparable problems? Can you reuse experience or tools?
9. Is human expertise available?
10. How would you solve the problem manually?
11. List the assumptions you (or others) have made so far.
12. Verify assumptions if possible.

### 2. Get the data *(automate, so you can get fresh data easily)*
1. List the data you need and how much.
2. Find and document where to get it.
3. Check how much space it will take.
4. Check legal obligations; get authorization if necessary.
5. Get access authorizations.
6. Create a workspace with enough storage.
7. Get the data.
8. Convert it to a format you can easily manipulate (without changing the data itself).
9. Ensure sensitive information is deleted or protected (e.g. anonymized).
10. Check the size and type of data (time series, sample, geographical, etc.).
11. **Sample a test set, put it aside, and never look at it (no data snooping!).**

### 3. Explore the data *(get insights from a field expert)*
1. Create a copy for exploration (sample it down if needed).
2. Keep a notebook record of the exploration.
3. Study each attribute: name; type (categorical, int/float, bounded/unbounded, text, structured…); % missing; noisiness and type of noise (stochastic, outliers, rounding errors…); usefulness for the task; type of distribution (Gaussian, uniform, logarithmic…).
4. For supervised tasks, identify the target attribute(s).
5. Visualize the data.
6. Study the correlations between attributes.
7. Study how you would solve the problem manually.
8. Identify promising transformations.
9. Identify extra data that would be useful (go back to "Get the data").
10. Document what you have learned.

### 4. Prepare the data
*Work on copies; write functions for every transformation*, for five reasons: re-prepare fresh data easily; reuse in future projects; clean the test set; clean new live instances; treat preparation choices as hyperparameters.
1. **Clean**: fix or remove outliers (optional); fill missing values (zero, mean, median…) or drop rows/columns.
2. **Feature selection** (optional): drop attributes with no useful information.
3. **Feature engineering**: discretize continuous features; decompose features (categorical, date/time…); add promising transformations (log(x), sqrt(x), x², …); aggregate features into promising new ones.
4. **Feature scaling**: standardize or normalize.

### 5. Shortlist promising models
*With huge data, sample smaller training sets (this penalizes complex models like big NNs or RFs). Automate.*
1. Train many quick-and-dirty models from different categories (linear, naive Bayes, SVM, random forest, neural net…) with standard parameters.
2. Measure and compare performance with N-fold CV: **mean and standard deviation** across folds.
3. Analyze the most significant variables for each algorithm.
4. Analyze the types of errors: what data would a human have used to avoid them?
5. Do a quick round of feature selection and engineering.
6. Do one or two more quick iterations of steps 1–5.
7. **Shortlist the top three to five models, preferring models that make different types of errors.**

### 6. Fine-tune the system
*Use as much data as possible, especially toward the end. Automate.*
1. Fine-tune hyperparameters with cross-validation:
   - Treat data transformation choices as hyperparameters, especially when unsure (zeros vs median vs dropping rows).
   - **Prefer random search over grid search** unless there are very few values; for very long training, use **Bayesian optimization** (Gaussian process priors, Snoek et al.).
2. Try ensemble methods: combining your best models often beats running them individually.
3. Once confident, measure the final model on the test set to estimate the generalization error.
- **Warning: Don't tweak your model after measuring the generalization error: you would start overfitting the test set.**

### 7. Present your solution
1. Document what you have done.
2. Create a nice presentation; highlight the big picture first.
3. Explain why your solution achieves the business objective.
4. Present interesting points noticed along the way: what worked and what did not; your assumptions and the system's limitations.
5. Communicate key findings through beautiful visualizations or easy-to-remember statements (e.g. "the median income is the number-one predictor of housing prices").

### 8. Launch!
1. Get the solution production-ready (plug into production data inputs, write unit tests, etc.).
2. Write monitoring code to check live performance at regular intervals and alert when it drops:
   - Beware of slow degradation: **models "rot" as data evolves**.
   - Measuring performance may require a human pipeline (e.g. crowdsourcing).
   - Also monitor **input quality** (a malfunctioning sensor, another team's stale output), especially for online learning.
3. Retrain models regularly on fresh data (automate as much as possible).

## Mental Models
- The checklist is a **loop, not a line**: exploration sends you back to data collection; error analysis sends you back to feature engineering.
- **Everything that touches data becomes a function or pipeline step**, so preprocessing choices are tunable and reproducible in production.
- **Diversity in the shortlist** pays off later: models with different error types ensemble better (Ch 7).

## Anti-patterns
- Skipping framing: building a model without knowing how its output is used downstream.
- Exploring before splitting off the test set.
- Tuning only one model family.
- Tweaking after test-set evaluation.
- Launching without monitoring inputs and outputs, or without a retraining plan.

## Key Takeaways
1. Start every project by pulling out this checklist (Ch 2 does exactly this).
2. Frame with business metrics, minimum acceptable performance, and the current baseline.
3. Protect the test set from step 2 onward.
4. Shortlist 3–5 diverse models via CV (mean ± std), then tune with random search or Bayesian optimization, then ensemble.
5. Monitor live performance *and* input quality; automate retraining.

## Connects To
- **Ch 1**: main challenges (bad data / bad model), testing and validating.
- **Ch 2**: full worked example of every step.
- **Ch 7**: ensembles for step 6.
- **Ch 10/19**: Keras Tuner and Vertex AI hyperparameter tuning (Bayesian optimization).
