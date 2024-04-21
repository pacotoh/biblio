import datetime
from datetime import datetime
import pandas as pd
import glob

GR_DATA_PATH = '../../data/gr'


def join_data() -> pd.DataFrame:
    files = glob.glob(f'{GR_DATA_PATH}/*/*.csv')
    dfs = [pd.read_csv(file) for file in files]
    return pd.concat(dfs)


def export_data(df: pd.DataFrame) -> None:
    date = datetime.now().strftime('%Y%m%d%H%M%S')
    df.to_csv(f'{GR_DATA_PATH}/{date}.csv')


if __name__ == '__main__':
    data = join_data()
    export_data(data)
