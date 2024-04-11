An open source data storage solution for chip designs and their corresponding components, analyses, and simulations.

## Setting up database

### Local installation

1. Install gdatasea
    ```bash
    pip install -e .
    ```

> [!NOTE]
> Installs `pygraphviz` to render the database schema. Please install necessary dependencies by following [this](https://pygraphviz.github.io/documentation/stable/install.html) tutorial.


2. Initialize the database
    ```bash
    rebuild_db
    ```

------------------
## Database schema

![](https://github.com/gdsfactory/gdatasea/blob/main/gdatasea_db.svg)
