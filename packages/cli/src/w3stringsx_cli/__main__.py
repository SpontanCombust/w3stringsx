import os
import sys
import traceback

from w3stringsx_lib.logging import init_logger, get_logger, get_log_file_path
from w3stringsx_ioc import di
from w3stringsx_svc import (
    Configuration,
    StringKeyDiscoveryService,
    W3StringsEncoderLocator, FromConfigW3stringsEncoderLocatorHandler, AppDirW3StringsEncoderLocatorHandler, PathEnvW3stringsEncoderLocatorHandler,
    W3StringsEncoder,
    W3StringsManagerService,
    ScratchFolderService
)
from w3stringsx_cli.configuration import W3stringsxCliConfiguration
from w3stringsx_cli.cli import cli_main


def setup_services():
    config = W3stringsxCliConfiguration()

    container = di.container_builder()\
        .abstract_singleton(Configuration, W3stringsxCliConfiguration, config)\
        .singleton(W3StringsEncoder)\
        .singleton(StringKeyDiscoveryService)\
        .transitive_factory(W3StringsEncoderLocator, lambda resolver:
            W3StringsEncoderLocator()
            .with_handler(FromConfigW3stringsEncoderLocatorHandler(resolver.resolve(Configuration)))
            .with_handler(AppDirW3StringsEncoderLocatorHandler(resolver.resolve(Configuration)))
            .with_handler(PathEnvW3stringsEncoderLocatorHandler()))\
        .singleton_resource(ScratchFolderService)\
        .singleton(W3StringsManagerService)\
        .build()
    
    di.push_container(container)

    init_logger(config.app_dir.get_or_default())

def main():
    setup_services()

    logger = get_logger()
    try:
        cli_main()                
    except Exception as e:
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(-1)
    finally:
        di.release_resources()
        logger.info(f'Logs have been written into {get_log_file_path()}')


if __name__ == '__main__':
    main()
