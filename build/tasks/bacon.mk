# Copyright (C) 2017 Unlegacy-Android
# Copyright (C) 2017,2020 The LineageOS Project
# Copyright (C) 2018,2020 The PixelExperience Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Android 17: Do not implement or re-sign an OTA here. Require AOSP's
# otapackage target and copy its finished archive byte-for-byte.
CUSTOM_TARGET_PACKAGE := $(PRODUCT_OUT)/$(CUSTOM_VERSION).zip

.PHONY: bacon
bacon: otapackage
	$(hide) python3 vendor/aosp/tools/a17_bacon_package.py \
		--ota "$(INTERNAL_OTA_PACKAGE_TARGET)" \
		--output "$(CUSTOM_TARGET_PACKAGE)"
