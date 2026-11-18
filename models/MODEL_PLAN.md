# Model & Experiment Plan

## 1. Problem as classification
In this project, map matching is framed as a supervised binary classification task. Each sample (row) in our tabular dataset represents a unique pair of an observed GPS point and a candidate road segment retrieved within a spatial search radius. The target label is 1 if that candidate segment is the true road traversed by the vehicle (matching the ground-truth route sequence), and 0 if it is an incorrect candidate or distractor.

## 2. Five models
To explore diverse algorithmic behaviors, we evaluate five models from five distinct machine learning families:

1. **Linear Models — Logistic Regression:** Serves as a fast, highly interpretable baseline whose sigmoid outputs naturally provide well-calibrated class probabilities that can directly feed into HMM emission scoring.
2. **Ensemble / Bagging — Random Forest Classifier:** Handles non-linear feature thresholds (e.g., sharp cutoffs in distance and orientation deltas) and is resilient to noisy GPS coordinate outliers without requiring feature scaling.
3. **Ensemble / Boosting — LightGBM (or XGBoost / Gradient Boosting):** Excels at tabular learning on imbalanced candidate data by iteratively focusing on hard-to-distinguish parallel road candidates and optimizing tree depth efficiently.
4. **Distance / Instance-based — K-Nearest Neighbors (KNN Classifier):** Leverages geometric and spatial proximity directly, naturally capturing local spatial density and neighborhood similarity across coordinate clusters.
5. **Kernel Methods / Non-linear Margin — Support Vector Classifier (SVC with RBF Kernel):** Maximizes the margin of separation in higher-dimensional projection space to cleanly differentiate between true road segments and nearby parallel candidate segments in dense urban canyons.

## 3. Metrics
The required metrics to report across our experiments are:
- **Accuracy:** The overall proportion of correctly classified candidates (True Positives + True Negatives over total pairs).
- **Precision:** The proportion of predicted positive candidates that are truly on the route, minimizing false road snapping.
- **Recall:** The proportion of actual route segments correctly identified among all candidate pools.
- **F1-Score:** The harmonic mean of precision and recall.
- **ROC-AUC & PR-AUC:** Area under the ROC and Precision-Recall curves to assess ranking quality across decision thresholds.
- **Route Connectivity (%):** The percentage of consecutive matched road segments that form a topologically valid, unbroken chain in the road network graph.

**Primary Metric Choice:**  
The **Primary Metric** must be the **F1-Score (specifically accompanied by PR-AUC)**. Because each GPS point has multiple candidate road segments (only one of which is positive), the dataset suffers from severe class imbalance where negatives heavily outnumber positives. Standard accuracy is misleadingly high simply by predicting negative everywhere. F1-Score penalizes both false segment attributions and missed road segments, providing the most reliable indicator of map-matching fidelity before final Viterbi decoding.

## 4. GroupKFold
GroupKFold is a cross-validation strategy that ensures all samples belonging to the same group are allocated exclusively to either the training split or the validation split, never spread across both. 

In our trajectory dataset, we **group by trip (`trip_id`)**. Because GPS points within a single trip share strong spatial-temporal correlations, vehicle dynamics, and identical road network neighborhoods, standard random K-Fold splitting would leak local road geometry into the validation set. Grouping by trip guarantees that the model is strictly evaluated on its ability to generalize to completely unseen vehicle trajectories and unfamiliar road configurations.

## 5. Rules to follow
- **80 Train Trips:** These trips constitute our sole training and cross-validation universe. All exploratory data analysis (EDA), feature extraction, candidate generation, hyperparameter tuning, and cross-validation must strictly be performed on this set.
- **10 Student Test Trips (`student_test`):** Must be treated strictly as blind evaluation data. No training, feature scaling fitting, or pseudo-labeling is permitted using reference routes from this split. Our model pipeline must process only their `.track`, `.nodes`, and `.arcs` files to produce final `.route` predictions.
- **Hidden Evaluator Trips:** Used solely by course evaluators for final grading and leaderboard scoring. The code must be cleanly modularized and automated so that any unseen trip directory with `.track`, `.nodes`, and `.arcs` can be parsed through the pipeline without hardcoded identifiers or manual interventions.
