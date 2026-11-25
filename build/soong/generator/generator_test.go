// Copyright (C) 2026 PixelExperience-Reborn
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package generator

import (
	"strings"
	"testing"

	"android/soong/android"
)

const kernelIncludesBp = `
custom_generator {
    name: "generated_kernel_includes",
    cmd: "$(KERNEL_MAKE_CMD) -C $(TARGET_KERNEL_HEADERS) O=$(KERNEL_BUILD_OUT_PREFIX)$(genDir) ARCH=$(KERNEL_ARCH) headers_install",
    export_include_dirs: ["usr/include"],
    dep_root: "$(TARGET_KERNEL_HEADERS)",
    dep_files: ["Makefile", "include/**/*"],
}
`

var prepareForGeneratorTest = android.GroupFixturePreparers(
	android.PrepareForTestWithArchMutator,
	android.FixtureRegisterWithContext(func(ctx android.RegistrationContext) {
		ctx.RegisterModuleType("custom_generator", GeneratorFactory)
	}),
	android.FixtureMergeMockFs(android.MockFS{
		"kernel/xiaomi/sm8450/Makefile":                   nil,
		"kernel/xiaomi/sm8450/include/uapi/linux/types.h": nil,
		"kernel/xiaomi/sm8450/include/uapi/linux/ioctl.h": nil,
	}),
)

func kernelVars(vars map[string]string) android.FixturePreparer {
	return android.FixtureModifyProductVariables(func(v android.FixtureProductVariables) {
		v.VendorVars = map[string]map[string]string{"customVarsPlugin": vars}
	})
}

// With the kernel exported by the board, the module installs the headers
// with the expanded make command inside sbox, depends on the globbed kernel
// sources and exports the requested include directories.
func TestKernelHeadersWithBoardVariables(t *testing.T) {
	result := android.GroupFixturePreparers(
		prepareForGeneratorTest,
		kernelVars(map[string]string{
			"KERNEL_MAKE_CMD":         "make",
			"TARGET_KERNEL_HEADERS":   "kernel/xiaomi/sm8450",
			"KERNEL_BUILD_OUT_PREFIX": "/top/",
			"KERNEL_ARCH":             "arm64",
		}),
		android.FixtureWithRootAndroidBp(kernelIncludesBp),
	).RunTest(t)

	gen := result.ModuleForTests(t, "generated_kernel_includes", "")
	module := gen.Module().(*Module)

	android.AssertPathsRelativeToTopEquals(t, "include dirs",
		[]string{"out/soong/.intermediates/generated_kernel_includes/gen/usr/include"},
		module.GeneratedHeaderDirs())
	android.AssertPathsRelativeToTopEquals(t, "deps",
		[]string{"out/soong/.intermediates/generated_kernel_includes/gen/.dummy_dep"},
		module.GeneratedDeps())

	manifest := android.RuleBuilderSboxProtoForTests(t, result.TestContext,
		gen.Output("custom.sbox.textproto"))
	cmd := android.StringRelativeToTop(result.Config, manifest.Commands[len(manifest.Commands)-1].GetCommand())
	for _, want := range []string{"make -C kernel/xiaomi/sm8450", "ARCH=arm64", "headers_install",
		"O=/top/out/soong/.intermediates/generated_kernel_includes/gen"} {
		if !strings.Contains(cmd, want) {
			t.Errorf("command %q does not contain %q", cmd, want)
		}
	}

	rule := gen.Rule("generator")
	android.AssertStringListContains(t, "kernel Makefile is an input",
		rule.RelativeToTop().Implicits.Strings(), "kernel/xiaomi/sm8450/Makefile")
	android.AssertStringListContains(t, "globbed kernel header is an input",
		rule.RelativeToTop().Implicits.Strings(), "kernel/xiaomi/sm8450/include/uapi/linux/types.h")
}

// Without kernel variables (a product that builds no kernel) the analysis
// must still succeed; only building the headers fails, naming the missing
// board variables.
func TestKernelHeadersWithoutBoardVariables(t *testing.T) {
	result := android.GroupFixturePreparers(
		prepareForGeneratorTest,
		android.FixtureWithRootAndroidBp(kernelIncludesBp),
	).RunTest(t)

	gen := result.ModuleForTests(t, "generated_kernel_includes", "")
	if out := gen.MaybeOutput("custom.sbox.textproto"); out.Rule != nil {
		t.Errorf("no sbox command must be generated without board variables")
	}
	dummy := gen.Output(".dummy_dep")
	if !android.IsErrorRule(dummy.Rule) {
		t.Fatalf("expected an error rule for .dummy_dep, got %v", dummy.Rule)
	}
	msg := dummy.Args["error"]
	for _, name := range []string{"KERNEL_ARCH", "KERNEL_BUILD_OUT_PREFIX", "KERNEL_MAKE_CMD", "TARGET_KERNEL_HEADERS"} {
		if !strings.Contains(msg, name) {
			t.Errorf("error message %q does not name %s", msg, name)
		}
	}
}
