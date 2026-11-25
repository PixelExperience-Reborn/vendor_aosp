// Copyright 2015 Google Inc. All rights reserved.
// Copyright (C) 2018,2021 The LineageOS Project
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

// Package generator provides custom_generator, a genrule-like module whose
// command may use board variables exported through the customVarsPlugin
// Soong config namespace (vendor/aosp/config/BoardConfigSoong.mk). It is
// used to install the kernel UAPI headers (generated_kernel_includes) that
// Qualcomm HALs consume through generated_kernel_headers.
//
// Ported to the Android 17 Soong API: dependencies are visited through
// module proxies and providers, tool_files are path properties, source
// paths come from PathForSource and the rule runs in sbox without input
// sandboxing (the kernel make reads the whole kernel tree).
package generator

import (
	"fmt"
	"path/filepath"
	"sort"
	"strings"

	"github.com/google/blueprint"
	"github.com/google/blueprint/proptools"

	"android/soong/android"
)

func init() {
	android.RegisterModuleType("custom_generator", GeneratorFactory)
}

var String = proptools.String

var pctx = android.NewPackageContext("aosp/soong/generator")

type hostToolDependencyTag struct {
	blueprint.BaseDependencyTag
}

var hostToolDepTag hostToolDependencyTag

type generatorProperties struct {
	// The command to run. Cmd supports substitution of a few variables
	// (the actual substitution is implemented in GenerateAndroidBuildActions below)
	//
	// Available variables for substitution:
	//
	//  $(location): the path to the first entry in tools or tool_files
	//  $(location <label>): the path to the tool or tool_file with name <label>
	//  $(genDir): the output directory of this module
	//  $(NAME): any variable exported in the customVarsPlugin namespace
	//  $$: a literal $
	Cmd *string

	// Name of the modules (if any) that produce the host executable. Leave empty for
	// prebuilts or scripts that do not need a module to build them.
	Tools []string

	// Local files that are used as tools.
	Tool_files []string `android:"path"`

	// List of directories to export as headers.
	Export_include_dirs []string

	// List of directories to export as sources.
	Export_source_dirs []string

	// Root directory for dep_files, relative to the top of the source tree.
	// May use customVarsPlugin variables. Defaults to the module directory.
	Dep_root *string

	// Globs, relative to dep_root, of files used for timestamp dependency checking.
	// May use customVarsPlugin variables.
	Dep_files []string
}

type Module struct {
	android.ModuleBase

	properties generatorProperties

	exportedIncludeDirs android.Paths
	exportedSourceDirs  android.Paths
	outputDeps          android.Paths
}

// These methods implement android.SourceFileGenerator. ModuleBase publishes
// them as CommonModuleInfo.GeneratedSource, which is what cc modules read for
// generated_headers / generated_sources on Android 17.
func (g *Module) GeneratedHeaderDirs() android.Paths {
	return g.exportedIncludeDirs
}

func (g *Module) GeneratedSourceFiles() android.Paths {
	return g.exportedSourceDirs
}

func (g *Module) GeneratedDeps() android.Paths {
	return g.outputDeps
}

var _ android.SourceFileGenerator = (*Module)(nil)

func (g *Module) DepsMutator(ctx android.BottomUpMutatorContext) {
	// tool_files are path properties: their ":module" references are added
	// automatically. dep_files are globs relative to dep_root, not module
	// references, so they add no dependencies here.
	if len(g.properties.Tools) > 0 {
		ctx.AddFarVariationDependencies(ctx.Config().BuildOSTarget.Variations(),
			hostToolDepTag, g.properties.Tools...)
	}
}

func exportedDirs(ctx android.ModuleContext, dirs []string) android.Paths {
	if len(dirs) == 0 {
		return android.Paths{android.PathForModuleGen(ctx, "")}
	}
	var paths android.Paths
	for _, dir := range dirs {
		paths = append(paths, android.PathForModuleGen(ctx, dir))
	}
	return paths
}

func (g *Module) GenerateAndroidBuildActions(ctx android.ModuleContext) {
	g.exportedIncludeDirs = exportedDirs(ctx, g.properties.Export_include_dirs)
	g.exportedSourceDirs = exportedDirs(ctx, g.properties.Export_source_dirs)

	tools := map[string]android.Path{}
	var implicitDeps android.Paths

	if len(g.properties.Tools) > 0 {
		ctx.VisitDirectDepsProxy(func(module android.ModuleProxy) {
			if ctx.OtherModuleDependencyTag(module) != hostToolDepTag {
				return
			}
			tool := ctx.OtherModuleName(module)
			info := android.GetHostToolInfo(ctx, module)
			if info == nil || !info.HostToolPath.Valid() {
				if ctx.Config().AllowMissingDependencies() {
					ctx.AddMissingDependencies([]string{tool})
				} else {
					ctx.ModuleErrorf("%q is not a host tool provider with an output file", tool)
				}
				return
			}
			path := info.HostToolPath.Path()
			if _, exists := tools[tool]; exists {
				ctx.ModuleErrorf("multiple tools for %q, %q and %q", tool, tools[tool], path)
				return
			}
			tools[tool] = path
			implicitDeps = append(implicitDeps, path)
		})
	}

	if ctx.Failed() {
		return
	}

	toolFiles := android.PathsForModuleSrc(ctx, g.properties.Tool_files)
	for _, tool := range toolFiles {
		implicitDeps = append(implicitDeps, tool)
		if _, exists := tools[tool.Rel()]; exists {
			ctx.ModuleErrorf("multiple tools for %q, %q and %q", tool, tools[tool.Rel()], tool.Rel())
			continue
		}
		tools[tool.Rel()] = tool
	}

	// Board variables (customVarsPlugin) that this module needs but the
	// product did not export. They are collected instead of failing the
	// analysis of every product: only building this module's output fails.
	unresolved := map[string]bool{}
	expand := func(in string) string {
		out, missing := customExpandVariables(ctx, in)
		for _, name := range missing {
			unresolved[name] = true
		}
		return out
	}

	// Root directory for dep_files. Defaults to the module directory.
	depRoot := String(g.properties.Dep_root)
	if depRoot == "" {
		depRoot = ctx.ModuleDir()
	} else {
		depRoot = expand(depRoot)
	}

	var inputDeps android.Paths
	if len(unresolved) == 0 {
		for _, depFile := range g.properties.Dep_files {
			globPath := filepath.Join(depRoot, expand(depFile))
			if len(unresolved) > 0 {
				break
			}
			paths, err := ctx.GlobWithDeps(globPath, nil)
			if err != nil {
				ctx.ModuleErrorf("unable to glob %s: %s", globPath, err.Error())
				return
			}
			for _, path := range paths {
				inputDeps = append(inputDeps, android.PathForSource(ctx, path))
			}
		}
	}

	exCmd := expand(String(g.properties.Cmd))

	// Placeholder output that dependents use to order after the command.
	dummyDep := android.PathForModuleGen(ctx, ".dummy_dep")
	g.outputDeps = android.Paths{dummyDep}

	rawCommand, err := android.Expand(exCmd, func(name string) (string, error) {
		switch name {
		case "location":
			if len(g.properties.Tools) == 0 && len(toolFiles) == 0 {
				return "", fmt.Errorf("at least one `tools` or `tool_files` is required if $(location) is used")
			}
			if len(g.properties.Tools) > 0 {
				return tools[g.properties.Tools[0]].String(), nil
			}
			return tools[toolFiles[0].Rel()].String(), nil
		case "genDir":
			return android.PathForModuleGen(ctx).String(), nil
		default:
			if strings.HasPrefix(name, "location ") {
				label := strings.TrimSpace(strings.TrimPrefix(name, "location "))
				if tool, ok := tools[label]; ok {
					return tool.String(), nil
				}
				return "", fmt.Errorf("unknown location label %q", label)
			}
			// A variable that customExpandVariables could not resolve.
			unresolved[name] = true
			return "", nil
		}
	})
	if err != nil {
		ctx.PropertyErrorf("cmd", "%s", err.Error())
		return
	}

	if len(unresolved) > 0 {
		names := make([]string, 0, len(unresolved))
		for name := range unresolved {
			names = append(names, name)
		}
		sort.Strings(names)
		android.ErrorRule(ctx, dummyDep, fmt.Sprintf(
			"%s: the board configuration does not export %s to the customVarsPlugin "+
				"Soong namespace (vendor/aosp/config/BoardConfigSoong.mk); "+
				"configure the kernel source before building modules that use it",
			ctx.ModuleName(), strings.Join(names, ", ")))
		return
	}

	genDir := android.PathForModuleGen(ctx)
	manifestPath := android.PathForModuleOut(ctx, "custom.sbox.textproto")

	// sbox wipes genDir before running the command and checks the declared
	// output. Input sandboxing is disabled because the command reads source
	// trees (for example the whole kernel) that are not declared inputs.
	rule := android.NewRuleBuilder(pctx, ctx).SandboxDisabled().Sbox(genDir, manifestPath)
	rule.Command().Text("touch").Output(dummyDep)
	cmd := rule.Command()
	cmd.Text(rawCommand)
	cmd.Implicits(inputDeps)
	cmd.Implicits(implicitDeps)

	rule.Build("generator", "generate "+ctx.ModuleName())
}

func NewGenerator() *Module {
	module := &Module{}
	module.AddProperties(&module.properties)
	return module
}

func GeneratorFactory() android.Module {
	m := NewGenerator()
	android.InitAndroidModule(m)
	return m
}
