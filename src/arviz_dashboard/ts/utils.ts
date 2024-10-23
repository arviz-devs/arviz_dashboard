export const getNestedObject = (nested_object: Object, path_array: Array<string>) => {
    return path_array.reduce((obj: Object, key: string) => {
        return obj && obj[key] !== "undefined" ? obj[key] : undefined
    }, nested_object)
}

export const sum = (data: number[]): number => {
    if (!data || data.length === 0) {
        return NaN
    } else {
        return data.reduce((total, current_value) => {
            return total + current_value
        })
    }
}

export const mean = (data: number[]): number => {
    if (!data || data.length === 0) {
        return NaN
    } else {
        return sum(data) / data.length
    }
}

export const std = (data: number[]): number => {
    if (!data || data.length === 0) {
        return NaN
    } else {
        const n = data.length
        const mu = mean(data)
        const variance_data = data.map((datum) => {
            return Math.pow(datum - mu, 2)
        })
        const variance = sum(variance_data) / n
        return Math.sqrt(variance)
    }
}

export const percentile = (data: number[], percent: number): number => {
    if (!data || data.length == 0) {
        return NaN
    }
    if (percent <= 0 || data.length < 2) {
        return data[0]
    }
    if (percent >= 100) {
        return data[data.length - 1]
    }
    const sorted_data = data.sort((a, b) => {
        return a - b
    })
    const N = sorted_data.length
    const index_float = (N - 1) * (percent / 100)
    const index = Math.floor(index_float)
    return data[index] + (data[index + 1] - data[index]) * (index_float - index)
}
