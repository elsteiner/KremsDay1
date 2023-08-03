
#= 
Test File 
Oegor Workshop
=#
zipcode = 4020


function affinect(x::Int64, b::Int64=9)
    println("Welcome to ", ifelse(zipcode==4020, "Linz", "Austria"))
    for a in "string", b in "hello"
        print(a, b, "-")
    end
    y = x^2 + b
    return y
end

println(affinect(2,9))

println("Hello Krems ")

