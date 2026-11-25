package generator

import (
	"fmt"

	"android/soong/android"
)

// customExpandVariables substitutes the board variables exported in the
// customVarsPlugin Soong config namespace. Variables that are not board
// variables are kept as $(NAME) for the generator's own expansion; the
// names of variables that were referenced but are not exported by the
// board are returned so the caller can report them.
func customExpandVariables(ctx android.ModuleContext, in string) (string, []string) {
	customVars := ctx.Config().VendorConfig("customVarsPlugin")
	var missing []string

	out, err := android.Expand(in, func(name string) (string, error) {
		if customVars.IsSet(name) {
			return customVars.String(name), nil
		}
		switch name {
		case "genDir", "location":
			return fmt.Sprintf("$(%s)", name), nil
		}
		if len(name) > len("location ") && name[:len("location ")] == "location " {
			return fmt.Sprintf("$(%s)", name), nil
		}
		// Referenced, but not exported by the board configuration.
		missing = append(missing, name)
		return fmt.Sprintf("$(%s)", name), nil
	})

	if err != nil {
		ctx.PropertyErrorf("cmd", "%s: %s", in, err.Error())
		return "", missing
	}

	return out, missing
}
