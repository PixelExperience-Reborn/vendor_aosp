# PixelExperience-Reborn Android 17: explicit AVB signing configuration.
# Included from config/BoardConfig.mk ONLY when the developer opted in
# with TARGET_USES_CUSTOM_AVB_KEY=true on an OFFICIAL/CI build.
# Never replace per-partition keys or disable verification implicitly.

ifneq ($(BOARD_AVB_ENABLE),true)
$(error PE custom AVB signing requires BOARD_AVB_ENABLE=true)
endif

ifeq ($(strip $(BOARD_AVB_KEY_PATH)),)
$(error PE custom AVB signing needs an explicitly configured BOARD_AVB_KEY_PATH)
endif
ifeq ($(strip $(BOARD_AVB_ALGORITHM)),)
$(error PE custom AVB signing needs an explicitly configured BOARD_AVB_ALGORITHM)
endif

# Disallow AOSP/public test keys for builds explicitly opting into release AVB.
pe_a17_forbidden_avb_key = $(filter external/avb/test/% build/make/target/product/security/%,$(strip $(1)))
pe_a17_avb_key_vars := BOARD_AVB_KEY_PATH BOARD_AVB_RECOVERY_KEY_PATH BOARD_AVB_VBMETA_SYSTEM_KEY_PATH BOARD_AVB_VBMETA_VENDOR_KEY_PATH
$(foreach k,$(pe_a17_avb_key_vars),$(if $(call pe_a17_forbidden_avb_key,$($(k))),$(error $(k) uses a public AOSP test key)))

# --flags can disable hashtree / verification (flags 1 and 2); never carry
# such flags into a configuration claiming to use custom release AVB keys.
ifneq ($(filter --flags --flags=%,$(BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS)),)
$(error PE custom AVB signing disallows BOARD_AVB_MAKE_VBMETA_IMAGE_ARGS --flags; inspect your device tree)
endif

# All configured private key files must already be provisioned by the maintainer.
# These checks verify only presence, NOT cryptographic validity / trust chain.
$(foreach k,$(pe_a17_avb_key_vars),$(if $(strip $($(k))),$(if $(wildcard $($(k))),,$(error $(k) points to a missing file))))

# Do NOT rewrite BOARD_AVB_KEY_PATH, BOARD_AVB_ALGORITHM, rollback indexes,
# vbmeta_system / vbmeta_vendor, recovery or any other per-partition keys.
