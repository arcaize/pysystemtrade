from dataclasses import dataclass

import pandas as pd
import numpy as np

from syscore.genutils import flatten_list

from sysquant.estimators.estimates import Estimates


class portfolioWeights(dict):

    @classmethod
    def allzeros(portfolioWeights, list_of_keys: list):
        return portfolioWeights.all_one_value(list_of_keys, value = 0.0)

    @classmethod
    def allnan(portfolioWeights, list_of_keys: list):
        return portfolioWeights.all_one_value(list_of_keys, value =np.nan)

    @classmethod
    def all_one_value(portfolioWeights, list_of_keys: list, value = 0.0):
        return portfolioWeights.from_weights_and_keys(list_of_weights=[value]*len(list_of_keys),
                                                      list_of_keys=list_of_keys)

    @classmethod
    def from_weights_and_keys( portfolioWeights,
                               list_of_weights: list,
                               list_of_keys: list):
        assert len(list_of_keys)==len(list_of_weights)
        pweights_as_list = [(key, weight) for key,weight in zip(list_of_keys, list_of_weights)]

        return portfolioWeights(pweights_as_list)

    @property
    def assets(self) -> list:
        return list(self.keys())

    def replace_weights_with_ints(self):
        new_weights_as_dict = dict([
            (instrument_code, _int_from_nan(value))
            for instrument_code, value in self.items()
        ])

        return portfolioWeights(new_weights_as_dict)

    def as_np(self) -> np.array:
        as_list = self.as_list()
        return np.array(as_list)

    def as_list(self) -> list:
        keys = list(self.keys())
        as_list = self.as_list_given_keys(keys)

        return as_list

    def as_list_given_keys(self, list_of_keys: list):
        return [self[key] for key in list_of_keys]

    @classmethod
    def from_list_of_subportfolios(portfolioWeights, list_of_portfolio_weights):
        list_of_unique_asset_names = \
            list(set(flatten_list([list(subportfolio.keys()) for subportfolio in list_of_portfolio_weights])))

        portfolio_weights = portfolioWeights.allzeros(list_of_unique_asset_names)

        for subportfolio_weights in list_of_portfolio_weights:
            for asset_name in list(subportfolio_weights.keys()):
                portfolio_weights[asset_name] = portfolio_weights[asset_name] + subportfolio_weights[asset_name]

        return portfolio_weights

    def with_zero_weights_for_missing_keys(self, list_of_asset_names):
        all_assets = list(set(list_of_asset_names + list(self.keys())))
        return portfolioWeights(dict([
            (key, self.get(key, 0))
            for key in all_assets
        ]))

    def with_zero_weights_instead_of_nan(self):
        all_assets = self.keys()
        def _replace(x):
            if np.isnan(x):
                return 0.0
            else:
                return x

        return portfolioWeights(dict([
            (key, _replace(self[key]))
            for key in all_assets
        ]))

    def assets_with_data(self) -> list:
        return [key for key, value in self.items() if not np.isnan(value)]

    def __truediv__(self, other: 'portfolioWeights'):
        return self._operate_on_other(other, "__truediv__")

    def __mul__(self, other: 'portfolioWeights'):
        return self._operate_on_other(other, "__mul__")

    def _operate_on_other(self, other: 'portfolioWeights', func_to_use):
        asset_list = self.assets
        np_self = np.array(self.as_list_given_keys(asset_list))
        np_other =  np.array(other.as_list_given_keys(asset_list))

        np_func = getattr(np_self, func_to_use)
        np_results = np_func(np_other)

        return portfolioWeights.from_weights_and_keys(list_of_weights=list(np_results),
                                                  list_of_keys=asset_list)



def _int_from_nan(x: float):
    if np.isnan(x):
        return 0
    else:
        return int(x)


@dataclass()
class estimatesWithPortfolioWeights():
    estimates: Estimates
    weights: portfolioWeights

def one_over_n_portfolio_weights_from_estimates(estimate: Estimates) -> portfolioWeights:
    mean_estimate = estimate.mean
    asset_names = list(mean_estimate.keys())
    return one_over_n_weights_given_asset_names(asset_names)


def one_over_n_weights_given_data(data: pd.DataFrame):
    list_of_asset_names = list(data.columns)

    return one_over_n_weights_given_asset_names(list_of_asset_names)

def one_over_n_weights_given_asset_names(list_of_asset_names: list) -> portfolioWeights:
    weight = 1.0 / len(list_of_asset_names)
    return portfolioWeights([(asset_name, weight) for asset_name in list_of_asset_names])
