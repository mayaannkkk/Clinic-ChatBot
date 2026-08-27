from sklearn.base import (
    BaseEstimator,
    TransformerMixin
)

import pandas as pd
import numpy as np


class FeatureEngineering(
    BaseEstimator,
    TransformerMixin
):

    def fit(
        self,
        X,
        y=None
    ):
        return self

    def transform(
        self,
        X
    ):

        X = X.copy()

        X["visit_dt"] = pd.to_datetime(
            X["Date"] + " " + X["Visit Time"],
            format="%Y-%m-%d %I:%M %p"
        )

        X["hour"] = (
            X["visit_dt"]
            .dt.hour
        )

        X["day_of_week"] = (
            X["visit_dt"]
            .dt.dayofweek
        )
        
        X["session"] = np.where(
            X["hour"] < 12,
            "Morning",
            "Evening"
        )

        return X[
            [
                "hour",
                "day_of_week",
                "session"
            ]
        ]