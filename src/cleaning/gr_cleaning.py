import datetime
from datetime import datetime
import pandas as pd
import glob
import ast
import numpy as np

GR_DATA_PATH = '../../data/gr'


def join_data() -> pd.DataFrame:
    files = glob.glob(f'{GR_DATA_PATH}/*/*.csv')
    dfs = [pd.read_csv(file) for file in files]
    return pd.concat(dfs)


def export_data(df: pd.DataFrame) -> None:
    date = datetime.now().strftime('%Y%m%d%H%M%S')
    df.to_csv(f'{GR_DATA_PATH}/{date}.csv')


def clean_first_step(df: pd.DataFrame) -> pd.DataFrame:
    info = df.drop(['title',
                    'desc',
                    'pub_info',
                    'cover',
                    'id',
                    'publication_timestamp',
                    'isbn',
                    'isbn13'], axis=1)

    info['authors'] = info['authors'].map(lambda x: set(ast.literal_eval(x)))
    info['rating_value'] = info['rating_value'].map(lambda x: int(x*100))
    info['num_pages'] = info['num_pages'].convert_dtypes()
    info['num_pages'] = info['num_pages'].replace('<NA>', np.nan)
    info = info[~info['publisher'].isna()]

    return info


def clean_counts(df: pd.DataFrame) -> pd.DataFrame:
    df['rating_count'] = df['rating_count'].convert_dtypes()
    df.fillna({'rating_count': 0}, inplace=True)

    df['review_count'] = df['review_count'].convert_dtypes()
    df.fillna({'review_count': 0}, inplace=True)

    return df


def clean_genres(df: pd.DataFrame) -> pd.DataFrame:
    pass


def clean_format(df: pd.DataFrame) -> pd.DataFrame:
    pass


if __name__ == '__main__':
    data = join_data()
    df_cleaned = clean_first_step(data)
    print(df_cleaned)
