from adapters.base import BaseAdapter
from adapters.weworkremotely import WeWorkRemotelyAdapter
from adapters.dynamitejobs import DynamiteJobsAdapter
from adapters.jobicy import JobicyAdapter
from adapters.workingnomads import WorkingNomadsAdapter
from adapters.jobspresso import JobspressoAdapter
from adapters.himalayas import HimalayasAdapter
from adapters.remotesource import RemoteSourceAdapter

ALL_ADAPTERS = [
    WeWorkRemotelyAdapter,
    DynamiteJobsAdapter,
    JobicyAdapter,
    WorkingNomadsAdapter,
    JobspressoAdapter,
    HimalayasAdapter,
    RemoteSourceAdapter,
]

__all__ = [
    "BaseAdapter",
    "ALL_ADAPTERS",
    "WeWorkRemotelyAdapter",
    "DynamiteJobsAdapter",
    "JobicyAdapter",
    "WorkingNomadsAdapter",
    "JobspressoAdapter",
    "HimalayasAdapter",
    "RemoteSourceAdapter",
]
