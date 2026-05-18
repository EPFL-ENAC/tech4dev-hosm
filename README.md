# HOSM Nepal – Dataset annotation tools

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) Python package and project manager
- [npm](https://docs.npmjs.com/) Node.js package manager
- Make


## Deploying locally


Clone the repository with submodules:

```bash
git clone
cd tech4dev-hosm
git submodule update --init
```

Setup your environment by running:

```bash
make install
```


### Backend

In one shell, run:

```bash
make run-db
make run-backend
```

The interactive API documentation will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

### Frontend

In another shell, run:

```bash
make run-frontend
```

The website will be available at [http://localhost:9000](http://localhost:9000).


## Development

### Annotation library

This project uses a [custom fork of Annotorious](https://github.com/EPFL-ENAC/annotorious) that adds undo functionality during polygon creation. To update and publish the Annotorious package:

```bash
# From the cloned Annotorious repository
npm install
npm run build
npm pack --workspaces
gh release create <tag> *.tgz
```


### Generate test data

To generate test data, run the following command after starting the database:

```bash
make generate-mock-data
```


### Generate tiles

To generate .dzi tiles for a directory of images (recursively), run the following command:

```bash
make generate-tiles <input_directory> <output_directory>
```

Existing tiles will be skipped.
