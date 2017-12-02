"""
A script to obtain the Ashlock Fingerprints of all strategies in the Axelrod
library.

This writes a hash of the source code of each strategy to file: db.csv.

If the source code of a strategy changes **or** a new strategy is introduced
then the fingerprint is regenerated for that strategy.
"""

import inspect
import hashlib
import csv
import string

import numpy as np
import matplotlib.pyplot as plt

import axelrod as axl
import axelrod_fortran as axlf


def hash_strategy(strategy):
    """
    Hash the source code of a strategy
    """
    try:
        source_code = "".join(inspect.getsourcelines(strategy)[0])
    except OSError:  # Some classes are dynamically created
        source_code = "".join(inspect.getsourcelines(strategy.strategy)[0])
    except TypeError:  # For the fortran strategies a player instance is passed
        source_code = "".join(strategy.original_name)
    hash_object = hashlib.md5(source_code.encode('utf-8'))
    hashed_source = hash_object.hexdigest()
    return hashed_source


def write_strategy_to_db(strategy, filename="db.csv", fingerprint="Ashlock"):
    """
    Write the hash of a strategy to the db
    """
    hashed_source = hash_strategy(strategy)
    with open(filename, "a") as db:
        try:
            db.write("{},{},{}\n".format(strategy.original_name, fingerprint, hashed_source))
        except AttributeError:
            db.write("{},{},{}\n".format(strategy.name, fingerprint, hashed_source))


def read_db(filename="db.csv"):
    """
    Read filename and return a dictionary mapping string names to hash of source
    code of a strategy
    """
    with open(filename, "r") as db:
        csvreader = csv.reader(db)
        str_to_hash = {(row[0], row[1]): row[2] for row in csvreader}
    return str_to_hash


def create_db(filename="db.csv"):
    """
    Creates an empty db.csv file
    """
    with open(filename, "w"):
        pass


def write_data_to_file(fp, filename):
    """
    Write the fingerprint data to a file.
    """
    columns = ['x', 'y', 'score']

    with open(filename, 'w') as f:
        w = csv.writer(f)
        w.writerow(columns)
        for key, value in fp.data.items():
            w.writerow([key.x, key.y, value])


def obtain_fingerprint(strategy, turns, repetitions, probe=axl.TitForTat):
    """
    Obtain the fingerprint for a given strategy and save the figure to the
    assets dir
    """
    fp = axl.AshlockFingerprint(strategy, probe)
    fp.fingerprint(turns=turns, repetitions=repetitions,
                   progress_bar=False, processes=0)
    plt.figure()
    fp.plot()
    try:
        name = strategy.original_name
    except AttributeError:
        name = strategy.name
    plt.tight_layout()
    plt.savefig("assets/{}.png".format(format_filename(name)),
                bbox_inches="tight")
    write_data_to_file(fp,
                       "assets/{}.csv".format(format_filename(name)))


def obtain_transitive_fingerprint(strategy, turns, repetitions):
    """
    Obtain the transitive fingerprint
    for a given strategy and save the figure to the assets dir
    """
    fp = axl.TransitiveFingerprint(strategy, number_of_opponents=30)
    fp.fingerprint(turns=turns, repetitions=repetitions,
                   progress_bar=False, processes=0)
    plt.figure()
    fp.plot()
    try:
        name = strategy.original_name
    except AttributeError:
        name = strategy.name
    plt.tight_layout()
    plt.savefig("assets/transitive_{}.png".format(format_filename(name)),
                bbox_inches="tight")
    np.savetxt("assets/transitive_{}.csv".format(format_filename(name)),
               fp.data)


def obtain_transitive_fingerprint_v_short(strategy, turns, repetitions):
    """
    Obtain the transitive fingerprint against short run time
    for a given strategy and save the figure to the assets dir
    """
    short_run_time = [s() for s in axl.short_run_time_strategies]
    fp = axl.TransitiveFingerprint(strategy,
                                   opponents=short_run_time)
    fp.fingerprint(turns=turns, repetitions=repetitions,
                   progress_bar=False, processes=0)
    plt.figure()
    fp.plot(display_names=True)
    try:
        name = strategy.original_name
    except AttributeError:
        name = strategy.name
    plt.tight_layout()
    plt.savefig("assets/transitive_v_short_{}.png".format(format_filename(name)),
                bbox_inches="tight")
    np.savetxt("assets/transitive_v_short_{}.csv".format(format_filename(name)),
               fp.data)


def format_filename(s):
    """
    Take a string and return a valid filename constructed from the string.
    Uses a whitelist approach: any characters not present in valid_chars are
    removed. Also spaces are replaced with underscores.

    Note: this method may produce invalid filenames such as ``, `.` or `..`
    When I use this method I prepend a date string like '2009_01_15_19_46_32_'
    and append a file extension like '.txt', so I avoid the potential of using
    an invalid filename.

    Borrowed from https://gist.github.com/seanh/93666
    """
    valid_chars = "-_.() {}{}".format(string.ascii_letters, string.digits)
    filename = ''.join(c for c in s if c in valid_chars)
    filename = filename.replace(' ','_')
    return filename


def write_markdown(strategy):
    """
    Write a markdown section of a strategy.

    """
    try:
        name = strategy.original_name
    except AttributeError:
        name = strategy.name
    markdown = """

## {0}

![fingerprint of {0}](./assets/{1}.png)

[data (csv)](./assets/{1}.csv)

![Transitive fingerprint of {0}](./assets/transitive_{1}.png)

[data (csv)](./assets/transitive_{1}.csv)

![Transitive fingerprint of {0} against short run time](./assets/transitive_v_short_{1}.png)

[data (csv)](./assets/transitive_v_short_{1}.csv)
    """.format(name, format_filename(name))
    return markdown


def main(turns, repetitions, 
         transitive_turns, transitive_repetitions,
         transitive_v_short_turns, transitive_v_short_repetitions):
    """
    Fingerprint all strategies, if a strategy has already been fingerprinted it
    does not get rerun.
    """
    version = axl.__version__
    axlf_version = axlf.__version__

    markdown = """# Ashlock and transitive fingerprints

See:
[axelrod.readthedocs.io/en/latest/tutorials/further_topics/fingerprinting.html#fingerprinting](http://axelrod.readthedocs.io/en/latest/tutorials/further_topics/fingerprinting.html#fingerprinting)

All strategies included from Axelrod version {} and all strategies from
axelrod_fortran version {}

This README.md file is autogenerated by running:

```
$ python update_fingerprints.py
```

Each individual fingerprint can be obtained by running:

```python
import axelrod as axl
fp = axl.AshlockFingerprint(strategy, probe)
fp.fingerprint(turns={}, repetitions={})
fp.plot()
```

# Axelrod library fingerprints

    """.format(version, axlf_version, turns, repetitions)
    try:
        db = read_db()
    except FileNotFoundError:
        create_db()
        db = read_db()

    for strategy in axl.short_run_time_strategies:
        name = strategy.name
        signature = hash_strategy(strategy)
        fp = "Ashlock"
        if (name, fp) not in db or db[name, fp] != signature:
        #    obtain_fingerprint(strategy, turns, repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        fp = "Transitive"
        if (name, fp) not in db or db[name, fp] != signature:
            obtain_transitive_fingerprint(strategy,
                                          transitive_turns,
                                          transitive_repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        fp = "Transitive_v_short"
        if (name, fp) not in db or db[name, fp] != signature:
            obtain_transitive_fingerprint_v_short(strategy,
                                                  transitive_v_short_turns,
                                                  transitive_v_short_repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        markdown += write_markdown(strategy)

    markdown += """

# Second tournament fortran strategy fingerprints

"""

    for name in axlf.all_strategies:
        player = axlf.Player(name)
        name = player.original_name
        signature = hash_strategy(player)
        fp = "Ashlock"
        if (name, fp) not in db or db[name, fp] != signature:
        #    obtain_fingerprint(strategy, turns, repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        fp = "Transitive"
        if (name, fp) not in db or db[name, fp] != signature:
            obtain_transitive_fingerprint(strategy,
                                          transitive_turns,
                                          transitive_repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        fp = "Transitive_v_short"
        if (name, fp) not in db or db[name, fp] != signature:
            obtain_transitive_fingerprint_v_short(strategy,
                                                  transitive_turns,
                                                  transitive_repetitions)
            write_strategy_to_db(strategy, fingerprint=fp)

        markdown += write_markdown(strategy)

    with open("README.md", "w") as outfile:
        outfile.write(markdown)


if __name__ == "__main__":
    turns, repetitions = 200, 50
    transitive_turns, transitive_repetitions = 200, 50
    transitive_v_short_turns, transitive_v_short_repetitions = 200, 50
    main(turns, repetitions,
         transitive_turns, transitive_repetitions,
         transitive_v_short_turns, transitive_v_short_repetitions)
