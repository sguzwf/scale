(function () {
    'use strict';

    angular.module('scaleApp').factory('StrikeConfiguration', function (scaleConfig, StrikeIngestFile) {
        var StrikeConfiguration = function (version, workspace, monitor, files_to_ingest) {
            this.version = scaleConfig.strikeConfigurationVersion;
            this.workspace = workspace;
            this.monitor = monitor ? monitor : {
                type: '',
                region_name: '',
                credentials: {
                    access_key_id: '',
                    secret_access_key: ''
                }
            };
            this.files_to_ingest = files_to_ingest ? StrikeIngestFile.transformer(files_to_ingest) : [];
        };

        StrikeConfiguration.prototype = {

        };

        // static methods, assigned to class
        StrikeConfiguration.build = function (data) {
            if (data) {
                return new StrikeConfiguration(
                    data.version,
                    data.workspace,
                    data.monitor,
                    data.files_to_ingest
                );
            }
            return new StrikeConfiguration();
        };

        StrikeConfiguration.transformer = function (data) {
            if (angular.isArray(data)) {
                return data.map(StrikeConfiguration.build);
            }
            return StrikeConfiguration.build(data);
        };

        return StrikeConfiguration;
    });
})();
