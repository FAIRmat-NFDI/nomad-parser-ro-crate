#
# Copyright The NOMAD Authors.
#
# This file is part of NOMAD. See https://nomad-lab.eu for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
from pathlib import Path

import pytest
import structlog
from nomad.datamodel import EntryArchive
from structlog.testing import LogCapture

from nomad_parser_ro_crate.parsers.parser import ROCrateParser

if os.getenv('_PYTEST_RAISE', '0') != '0':

    @pytest.hookimpl(tryfirst=True)
    def pytest_exception_interact(call):
        raise call.excinfo.value

    @pytest.hookimpl(tryfirst=True)
    def pytest_internalerror(excinfo):
        raise excinfo.value


@pytest.fixture(scope='module')
def parser():
    """Fixture providing the RO-Crate parser."""
    return ROCrateParser()


@pytest.fixture
def test_data_path():
    """Fixture providing the path to test data."""
    return Path(__file__).parent / 'data'


@pytest.fixture
def simple_archive():
    """Fixture providing a clean EntryArchive for testing."""
    return EntryArchive()


@pytest.fixture
def log_output():
    """Fixture for capturing log output during tests."""
    capture = LogCapture()
    processors = structlog.get_config()['processors']
    old_processors = processors.copy()
    try:
        # clear processors list and use LogCapture for testing
        processors.clear()
        processors.append(capture)
        structlog.configure(processors=processors)
        yield capture
    finally:
        # remove LogCapture and restore original processors
        processors.clear()
        processors.extend(old_processors)
        structlog.configure(processors=processors)


@pytest.fixture
def approx():
    """Fixture for approximate value comparisons."""

    def func(expected, abs: float = 0.0, rel=1e-6):
        return pytest.approx(expected, abs=abs, rel=rel)

    return func


# Test data file constants for easy reference
SIMPLE_RO_CRATE = 'simple_ro_crate/ro-crate-metadata.json'
COMPLEX_RO_CRATE = 'complex_ro_crate/ro-crate-metadata.json'
NO_SCHEMA_RO_CRATE = 'no_schema_ro_crate/ro-crate-metadata.json'
INVALID_RO_CRATE = 'invalid_ro_crate.json'  # This file doesn't exist anymore
REAL_EXAMPLE_RO_CRATE = 'real_example_ro_crate/ro-crate-metadata.json'

# Expected counts for test data files
SIMPLE_RDFS_CLASSES = 1
SIMPLE_RDFS_PROPERTIES = 1
SIMPLE_DATA_INSTANCES = 2

COMPLEX_RDFS_CLASSES = 2
COMPLEX_RDFS_PROPERTIES = 3
COMPLEX_DATA_INSTANCES = 4

NO_SCHEMA_RDFS_CLASSES = 0
NO_SCHEMA_RDFS_PROPERTIES = 0
NO_SCHEMA_DATA_INSTANCES = 2  # root dataset + simple-data file (excludes CreativeWork)

INVALID_RDFS_CLASSES = 0
INVALID_RDFS_PROPERTIES = 0
INVALID_DATA_INSTANCES = 0

REAL_EXAMPLE_RDFS_CLASSES = 13
REAL_EXAMPLE_RDFS_PROPERTIES = 28
REAL_EXAMPLE_DATA_INSTANCES = 9
