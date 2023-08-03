
#= 
Test File 
Oegor Workshop
=#
zipcode = 4020

function affinect(x::Int64, b::Int64=9)
    println("Welcome to ", ifelse(zipcode==4020, "Linz", "Austria"))
    y = x^2 + b
    return y
end

println("Hello Krems ", affinect(2,9))

# ------------------------------------
using JuMP, Gurobi

# Declare and initialize model (empty)
model = Model(Gurobi.Optimizer)
# Define variables
@variable(model, x1>= 0)
@variable(model, x2>= 0)
# Define objective
@objective(model, Max, x1+ 3x2)
# Define contraints
@constraint(model, cst1, x1 + x2 <= 14)
@constraint(model, cst2, -2x1 +3x2 <=12)
@constraint(model, cst3, 2x1 - x2 <= 12)
@show(model)
print(model)
# Optimize
optimize!(model)
# Querying solution
if termination_status(model) == MOI.OPTIMAL
    zOpt = objective_value(model)
    @printf(" z=%5.2f x1=%5.2f x2=%5.2f \n",
             zOpt,
value(x1),
             value(x2))
    @printf(" u1=%5.2f u2=%5.2f u3=%5.2f \n",
             dual(cst1),
             dual(cst2),
             dual(cst3))
 elseif termination_status(model) == DUAL_INFEASIBLE
    println("problem unbounded")
 elseif termination_status(model) == MOI.INFEASIBLE
    println("problem infeasible")
end

