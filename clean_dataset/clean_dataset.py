import re
import click
import pandas as pd
from pathlib import Path
from datetime import date
import category_encoders as ce
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def _save_clean_dataset(clean_dataset, outdir: Path):
    """Save transformed data set into nice directory structure and write SUCCESS flag."""
    out_clean_dataset = outdir / 'clean.csv/'
    flag = outdir / '.SUCCESS'

    clean_dataset.to_csv(str(out_clean_dataset), index=False)

    flag.touch()

def get_compound(description, analyzerObj):
    compound = analyzerObj.polarity_scores(description)['compound']
    return compound

def get_year(title):
    if (re.search(r"(\d{4})", title)):
        year = int(re.search(r"(\d{4})", title).group(1))
        if (year <= date.today().year and year >= 1500):
            return year
    
    return 0

@click.command()
@click.option('--in-csv')
@click.option('--out-dir')
def clean_dataset(in_csv, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    df = pd.read_csv(in_csv)

    # drop irrelevant columns 
    df = df.drop(columns = ['Unnamed: 0', 'designation', 'region_2', 'taster_twitter_handle', 'winery'])
    # drop duplicates
    df = df.drop_duplicates(ignore_index=True)
    
    # extract new features
    analyzerObj = SentimentIntensityAnalyzer()
    df['descLen'] = df['description'].map(lambda description: len(description))
    df['compound'] = df['description'].map(lambda description: get_compound(description, analyzerObj))
    df['year'] = df['title'].map(lambda title: get_year(title))

    # fill null values
    df['price'].fillna(df['price'].median(), inplace=True)
    df['country'].fillna(str(df['country'].mode()), inplace=True)
    df['province'].fillna(str(df['province'].mode()), inplace=True)
    df['region_1'].fillna(str(df['region_1'].mode()), inplace=True)
    df['taster_name'].fillna(0, inplace=True)
    df['year'].replace(0, df.loc[df['year']>0].median()['year'], inplace = True)
    
    # encoding categorical features
    X = df.drop(columns=['description', 'title'])
    y = df['points']
    ce_ord = ce.OrdinalEncoder(cols = ['country', 'province', 'region_1', 'taster_name', 'variety'])
    X_labeled = ce_ord.fit_transform(X, y)
    
    # save transformed dataset to out_dir
    _save_clean_dataset(X_labeled, out_dir)


if __name__ == '__main__':
    clean_dataset()
